"""Adapters for the supplied YOLO image and Keras audio models."""
from __future__ import annotations

import gc
import pickle
import logging
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any

MODEL_DIR = Path(__file__).resolve().parents[2] / "models"
logger = logging.getLogger(__name__)

# Torch/Ultralytics and TensorFlow are both sizeable runtimes.  Keeping both
# model graphs alive in a small Render instance can exhaust its memory even
# when requests are handled one at a time.  Keep only the runtime used by the
# most recent request and release the other one before loading it.
_MODEL_LOCK = RLock()
_IMAGE_MODEL: Any | None = None
_AUDIO_MODEL: Any | None = None
_AUDIO_ENCODER: Any | None = None
_TENSORFLOW: Any | None = None

# The audio classifier was trained with scientific/taxonomic labels. Keep the
# model output intact, but expose the familiar common name in the product.
COMMON_NAME_BY_LABEL = {
    "equus caballus": "Horse", "equus asinus": "Donkey", "felis catus": "Cat",
    "canis lupus": "Wolf", "panthera leo": "Lion", "elephas maximus": "Elephant",
    "bos taurus": "Cattle", "ovis aries": "Sheep", "gallus gallus domesticus": "Chicken",
    "ursidae": "Bear", "anura": "Frog", "cercopithecidae": "Monkey",
    "cardinalis cardinalis": "Northern Cardinal", "carduelis carduelis": "Goldfinch",
    "passer domesticus": "House Sparrow", "corvus ossifragus": "Fish Crow",
    "larus californicus": "California Gull", "selasphorus rufus": "Rufous Hummingbird",
}

def common_name_for_label(label: str | None) -> str | None:
    if not label:
        return None
    cleaned = " ".join(label.replace("_", " ").split())
    return COMMON_NAME_BY_LABEL.get(cleaned.casefold(), cleaned.title())


class ModelUnavailableError(RuntimeError):
    """Raised when the trained artefacts required for an inference are absent."""

@dataclass(frozen=True)
class ImageBoxPrediction:
    species_name: str
    class_id: int
    confidence: float
    bbox: list[float]


def model_file(name: str) -> Path | None:
    candidate = MODEL_DIR / name
    return candidate if candidate.is_file() else None

def image_model():
    global _IMAGE_MODEL
    path = model_file("best.pt")
    if path is None:
        return None

    with _MODEL_LOCK:
        if _IMAGE_MODEL is not None:
            return _IMAGE_MODEL

        _release_audio_model()
        from ultralytics import YOLO

        logger.info("Loading YOLO image model from %s", path)
        model = YOLO(str(path))
        model.to("cpu")
        _IMAGE_MODEL = model
        logger.info("YOLO image model loaded successfully")
        return _IMAGE_MODEL


def audio_assets():
    global _AUDIO_MODEL, _AUDIO_ENCODER, _TENSORFLOW
    model_path, encoder_path = model_file("audio_model_v2_77.keras"), model_file("label_encoder_v2.pkl")
    if model_path is None or encoder_path is None: return None, None

    with _MODEL_LOCK:
        if _AUDIO_MODEL is not None and _AUDIO_ENCODER is not None:
            return _AUDIO_MODEL, _AUDIO_ENCODER

        _release_image_model()
        import tensorflow as tf

        _TENSORFLOW = tf
        # Inference does not need TensorFlow's default thread pool.  Limiting
        # it prevents a burst of worker threads from consuming the instance's
        # remaining memory on small CPU-only deployments.
        try:
            tf.config.threading.set_intra_op_parallelism_threads(1)
            tf.config.threading.set_inter_op_parallelism_threads(1)
        except RuntimeError:
            # The runtime may already be initialized after a previous request.
            pass

        with encoder_path.open("rb") as source:
            encoder = pickle.load(source)
        logger.info("Loading Keras audio model from %s", model_path)
        _AUDIO_MODEL = tf.keras.models.load_model(model_path, compile=False)
        _AUDIO_ENCODER = encoder
        logger.info("Keras audio model loaded successfully")
        return _AUDIO_MODEL, _AUDIO_ENCODER


def _release_image_model() -> None:
    global _IMAGE_MODEL
    if _IMAGE_MODEL is None:
        return
    logger.info("Releasing YOLO image model before audio inference")
    _IMAGE_MODEL = None
    gc.collect()


def _release_audio_model() -> None:
    global _AUDIO_MODEL, _AUDIO_ENCODER
    if _AUDIO_MODEL is None and _AUDIO_ENCODER is None:
        return
    logger.info("Releasing Keras audio model before image inference")
    _AUDIO_MODEL = None
    _AUDIO_ENCODER = None
    if _TENSORFLOW is not None:
        try:
            _TENSORFLOW.keras.backend.clear_session()
        except Exception:
            logger.debug("Unable to clear the TensorFlow session", exc_info=True)
    gc.collect()


def predict_image(path: str, annotated_path: str | None = None) -> list[ImageBoxPrediction]:
    with _MODEL_LOCK:
        model = image_model()
        if model is None:
            raise ModelUnavailableError("Image model file best.pt was not found. Add it to backend/models/ and restart the API.")
        results = model(path, device="cpu", imgsz=640, max_det=100, verbose=False)
        if annotated_path:
            from PIL import Image
            plotted = results[0].plot()
            Image.fromarray(plotted[..., ::-1]).save(annotated_path)
        boxes = results[0].boxes
        if boxes is None or len(boxes) == 0:
            logger.info("YOLO RAW DETECTIONS: []")
            logger.info("TOTAL RAW DETECTIONS: 0")
            return []
        predictions = []
        for box in boxes:
            class_id = int(box.cls.item())
            predictions.append(ImageBoxPrediction(
                species_name=str(model.names[class_id]), class_id=class_id,
                confidence=float(box.conf.item()), bbox=[float(v) for v in box.xyxy[0].tolist()],
            ))
        logger.info("YOLO RAW DETECTIONS: %s", [f"{p.species_name} | confidence={p.confidence:.4f} | bbox={p.bbox}" for p in predictions])
        logger.info("TOTAL RAW DETECTIONS: %d", len(predictions))
        return predictions


def predict_audio(path: str) -> tuple[str | None, float | None]:
    with _MODEL_LOCK:
        model, encoder = audio_assets()
        if model is None or encoder is None:
            raise ModelUnavailableError("Audio files audio_model_v2_77.keras and label_encoder_v2.pkl were not found. Add them to backend/models/ and restart the API.")
        import librosa
        import librosa.display
        import matplotlib
        import numpy as np
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from PIL import Image
        audio, sample_rate = librosa.load(path, sr=22050)
        mel = librosa.feature.melspectrogram(y=audio, sr=sample_rate)
        mel_db = librosa.power_to_db(mel, ref=np.max)
        figure, axis = plt.subplots(figsize=(2.24, 2.24), dpi=100)
        axis.axis("off")
        librosa.display.specshow(mel_db, sr=sample_rate, ax=axis)
        figure.tight_layout(pad=0)
        from io import BytesIO
        buffer = BytesIO()
        figure.savefig(buffer, format="png", bbox_inches="tight", pad_inches=0)
        plt.close(figure)
        buffer.seek(0)
        with Image.open(buffer) as image:
            spectrogram = image.convert("RGB").resize((224, 224))
        prediction = model.predict(np.expand_dims(np.asarray(spectrogram) / 255.0, axis=0), verbose=0)[0]
        index = int(np.argmax(prediction))
        raw_label = str(encoder.inverse_transform([index])[0])
        return common_name_for_label(raw_label), float(prediction[index])
