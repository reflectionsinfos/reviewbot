from app.services.autonomous_review.agent_orchestrator import _fallback_text_files, _validate_plan
from app.services.autonomous_review.connectors.agent_scan import AgentFileIndex


def _file_index():
    metadata = {
        "files": [
            {"path": "pom.xml", "size_bytes": 100, "language": "xml", "hash": "", "line_count": 5},
            {
                "path": r"src\main\java\com\sample\Application.java",
                "size_bytes": 200,
                "language": "java",
                "hash": "",
                "line_count": 10,
            },
        ]
    }
    content = {
        "pom.xml": "<project />",
        "src/main/java/com/sample/Application.java": "class Application {}",
    }
    return AgentFileIndex(metadata, content)


def test_agent_file_index_normalizes_windows_paths():
    file_index = _file_index()
    paths = [fi.rel_path for fi in file_index.files]
    assert "src/main/java/com/sample/Application.java" in paths
    assert file_index.get_content(r"src\main\java\com\sample\Application.java") == "class Application {}"


def test_validate_plan_accepts_agent_paths():
    file_index = _file_index()

    class Item:
        id = 1

    result = _validate_plan(
        [
            {
                "item_id": 1,
                "strategy": "llm_analysis",
                "complexity": "simple",
                "files_to_read": ["src/main/java/com/sample/Application.java"],
            }
        ],
        [Item()],
        file_index,
    )

    assert result[1].files == ["src/main/java/com/sample/Application.java"]


def test_fallback_text_files_returns_text_candidates():
    file_index = _file_index()
    assert _fallback_text_files(file_index, max_files=2) == [
        "pom.xml",
        "src/main/java/com/sample/Application.java",
    ]
