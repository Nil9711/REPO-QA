import sys
from pathlib import Path
from typing import Optional

from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import NodeWithScore, QueryBundle

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DEPLOYMENT_FILE_PATTERNS


def should_exclude_file(file_path: str) -> bool:
    path_lower = file_path.lower()
    return any(pattern in path_lower for pattern in DEPLOYMENT_FILE_PATTERNS)


class ExcludeDeploymentFilesPostprocessor(BaseNodePostprocessor):

    def _postprocess_nodes(
        self, nodes: list[NodeWithScore], query_bundle: Optional[QueryBundle] = None
    ) -> list[NodeWithScore]:
        return [
            node for node in nodes
            if not should_exclude_file(
                (node.node.metadata or {}).get("file_path") or
                (node.node.metadata or {}).get("filename") or ""
            )
        ]
