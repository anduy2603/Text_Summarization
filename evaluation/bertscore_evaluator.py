from __future__ import annotations

"""BERTScore evaluator for Vietnamese summarization."""

from typing import Any


BERTSCORE_DEFAULT_MODEL = "bert-base-multilingual-cased"


class BertScorer:
    """
    Wraps the bert_score library for Vietnamese summarization evaluation.

    Default model: bert-base-multilingual-cased (mBERT).
    This is the standard choice for Vietnamese in academic NLP papers and
    matches the multilingual setting of VietNews.

    num_layers=None lets bert_score pick the optimal layer per its internal
    hash table (layer 9 for mBERT, per BERTScore paper Table 3).
    """

    def __init__(
        self,
        model_type: str = BERTSCORE_DEFAULT_MODEL,
        num_layers: int | None = None,
        batch_size: int = 32,
        device: str | None = None,
        verbose: bool = True,
    ) -> None:
        try:
            import bert_score  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "bert_score not installed. Run: pip install bert-score"
            ) from exc
        self._model_type = model_type
        self._num_layers = num_layers
        self._batch_size = batch_size
        self._device = device
        self._verbose = verbose

    @property
    def model_type(self) -> str:
        return self._model_type

    def score_pairs(
        self,
        predictions: list[str],
        references: list[str],
    ) -> list[dict[str, float]]:
        """
        Compute BERTScore Precision / Recall / F1 for each (prediction, reference) pair.
        Returns a list of dicts: {"bertscore_p", "bertscore_r", "bertscore_f1"}.
        """
        if len(predictions) != len(references):
            raise ValueError(
                f"Length mismatch: {len(predictions)} predictions vs {len(references)} references"
            )
        if not predictions:
            return []

        from bert_score import score as _bert_score

        kwargs: dict[str, Any] = {
            "model_type": self._model_type,
            "batch_size": self._batch_size,
            "verbose": self._verbose,
        }
        if self._num_layers is not None:
            kwargs["num_layers"] = self._num_layers
        if self._device is not None:
            kwargs["device"] = self._device

        P, R, F = _bert_score(predictions, references, **kwargs)
        return [
            {
                "bertscore_p": float(p),
                "bertscore_r": float(r),
                "bertscore_f1": float(f),
            }
            for p, r, f in zip(P.tolist(), R.tolist(), F.tolist())
        ]
