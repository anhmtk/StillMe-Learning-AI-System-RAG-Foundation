"""
Embedding Worker for Windows Safety
===================================

Subprocess-based embedding worker to avoid Windows torch crashes.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path


class EmbeddingRuntimeError(Exception):
    """Custom exception for embedding runtime errors"""

    pass


class EmbeddingWorker:
    """Subprocess-based embedding worker for Windows safety"""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._worker_script = self._create_worker_script()
        self._timeout = 20  # 20 seconds timeout

    def _create_worker_script(self) -> Path:
        """Create the worker script"""
        script_content = """
import json
import os
import sys

# Set thread limits for Windows stability
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

try:
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    print(json.dumps({"error": f"Import failed: {e}"}))
    sys.exit(1)

def main():
    try:
        # Read input from stdin
        input_data = json.loads(sys.stdin.read())
        model_name = input_data.get("model", "sentence-transformers/all-MiniLM-L6-v2")
        texts = input_data.get("texts", [])

        # Load model
        model = SentenceTransformer(model_name)

        # Generate embeddings
        embeddings = model.encode(texts)

        # Convert to list format
        result = [emb.tolist() for emb in embeddings]

        # Output result
        print(json.dumps({"embeddings": result}))

    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()
"""

        # Write script to temporary file
        script_path = Path(tempfile.gettempdir()) / "embedding_worker.py"
        script_path.write_text(script_content)
        return script_path

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using subprocess worker"""
        if not texts:
            return []

        try:
            # Prepare input data
            input_data = {"model": self.model_name, "texts": texts}

            # Run worker subprocess
            result = subprocess.run(
                [sys.executable, str(self._worker_script)],
                input=json.dumps(input_data),
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )

            if result.returncode != 0:
                error_msg = result.stderr or "Unknown subprocess error"
                raise EmbeddingRuntimeError(f"Worker failed: {error_msg}")

            # Parse output
            try:
                output_data = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                raise EmbeddingRuntimeError(f"Invalid JSON output: {e}") from e

            if "error" in output_data:
                raise EmbeddingRuntimeError(f"Worker error: {output_data['error']}")

            if "embeddings" not in output_data:
                raise EmbeddingRuntimeError("No embeddings in output")

            return output_data["embeddings"]

        except subprocess.TimeoutExpired as e:
            raise EmbeddingRuntimeError(f"Worker timeout after {self._timeout}s") from e
        except Exception as e:
            if isinstance(e, EmbeddingRuntimeError):
                raise
            raise EmbeddingRuntimeError(f"Worker execution failed: {e}") from e

    def cleanup(self):
        """Cleanup worker script"""
        try:
            if self._worker_script.exists():
                self._worker_script.unlink()
        except Exception:
            pass  # Ignore cleanup errors
