import subprocess
import tempfile

from dict_typer import get_type_definitions

# fmt: off
TEST_SOURCE = {
    "manual_input": False,
    "source": {
        "user_id": "user-1",
        "path": "https://example.com",
        "thumbnails": {
            "xs": "https.example.com.xs_thumbnail.jpg",
            "sm": "https.example.com.sm_thumbnail.jpg",
            "md": "https.example.com.md_thumbnail.jpg",
            "lg": "https.example.com.lg_thumbnail.jpg",
            "xl": "https.example.com.xl_thumbnail.jpg",
        },
        "title": "Example Title",
        "description": "This is an example description.",
        "hosts": [
            {"name": "Sponsor Name", "id": "sponsor-1"},
            {"name": "Venue Name", "id": "venue-1"},
            {"name": "Institution Name", "id": "institution-1"},
        ],
        "authors": [
            {
                "name": "Author One",
                "id": "author-1",
            },
            {
                "name": "Speaker x",
                "id": "speaker-1",
            },
        ],
        "publication_date": {
            "year": 2023,
            "month": 10,
            "day": 15,
            "century": 21,
            "ad_bc": "AD",
        },
        "content_type": "text/html",
    },
    "markdown": {"text": "Example Markdown\n\nThis is an example markdown content."},
    "video": {
        "path": "https://example.com/video.mp4",
        "duration": 3600,
        "resolution": "1920x1080",
        "bitrate": 5000,
        "frame_rate": 30,
        "codec": "h264",
        "format": "mp4",
        "captions": {
            "path": "https://example.com/captions.srt",
            "language": "en",
            "format": "srt",
            "encoding": "utf-8",
            "is_auto_generated": False,
        },
    },
    "audio": {
        "path": "https://example.com/audio.mp3",
        "duration": 120,
        "bitrate": 128,
        "sample_rate": 44100,
        "channels": 2,
        "format": "mp3",
        "language": "en",
    },
    "paragraphs": [
        {
            "uuid": "paragraph-1",
            "antecedent_sim": 0.76,
            "heading": "heading-1",
            "text": "This is the first paragraph.",
            "timespan": [
                0,
                60.123,
            ],
            "line_numbers": [
                0,
                100,
            ],
            "page": 1,
            "embeddings": {
                "first_sentence": [0.1, 0.2, 0.3],
                "paragraph": [0.4, 0.5, 0.6],
                "last_sentence": [
                    0.7,
                    0.8,
                    0.9,
                ],
            },
        }
    ],
    "rdf": [
        {
            "triples": [
                {
                    "subject": {
                        "type": "node type",
                        "id": "💠 UUID of a matching node or new id if no match",
                        "sources": ["paragraph-1"],
                    },
                    "predicate": {
                        "type": "edge type",
                        "id": "💠 UUID of a matching edge or new id if no match",
                        "sources": ["paragraph-1"],
                    },
                    "object": {
                        "type": "edge type",
                        "id": "💠 UUID of a matching node or new id if no match",
                        "sources": ["paragraph-1"],
                    },
                }
            ]
        }
    ],
}
# fmt: on


def _line_numbered(string: str) -> str:
    lines = string.split("\n")
    return "\n".join([f"{idx+1:2}: {line}" for idx, line in enumerate(lines)])


def test_script_runs_with_nonzero() -> None:
    """A python e2e test

    1. Takes a source and converts it to a definition
    2. Adds a simple script to use the Type
    3. Saves the definition output into a Python file
    4. Runs the file to verify it runs
    """

    # 1.
    source_type_name = "Test"
    type_postfix = "Type"

    output = get_type_definitions(
        TEST_SOURCE,
        root_type_name=source_type_name,
        type_postfix=type_postfix,
        show_imports=True,
    )

    with open("tests/e2e/test_full.output_types.py", "w", encoding="utf-8") as f:
        f.write(output)
    # 2.
    input_string = f"test_source: {source_type_name}{type_postfix} = {TEST_SOURCE}"
    # fmt: off
    output += "\n".join([
        "",
        "",
        f"{input_string}",
        "print(test_source)",
    ])
    # fmt: on

    # 3.
    with tempfile.NamedTemporaryFile(suffix=".py") as f:
        f.write(output.encode("utf-8"))
        f.flush()

        # 4.
        with subprocess.Popen(["python", f.name], stdout=subprocess.PIPE) as proc:
            stdout, stderr = proc.communicate()
            assert not proc.returncode, "\n".join(
                [
                    "Non zero return code from script.",
                    "stderr:",
                    stderr and stderr.decode("utf-8") or "",
                    "Full script:",
                    "-" * 60,
                    _line_numbered(output),
                    "-" * 60,
                ]
            )

            assert stdout.decode("utf-8") == f"{TEST_SOURCE}\n"


def test_mypy_has_no_issues() -> None:
    """A mypy e2e test

    1. Takes a source and converts it to a definition
    2. Adds a simple script to use the Type
    3. Saves the definition output into a Python file
    4. Runs mypy on the script to verify there are no typing issues
    """

    # 1.
    source_type_name = "Test"
    type_postfix = "Type"

    output = get_type_definitions(
        TEST_SOURCE,
        root_type_name=source_type_name,
        type_postfix=type_postfix,
        show_imports=True,
    )

    # 2.
    input_string = f"test_source: {source_type_name}{type_postfix} = {TEST_SOURCE}"
    # fmt: off
    output += "\n".join([
        "",
        "",
        f"{input_string}",
        "print(test_source)",
    ])
    # fmt: on

    # 3.
    with tempfile.NamedTemporaryFile(suffix=".py") as f:
        f.write(output.encode("utf-8"))
        f.flush()

        # 4.

        # 4.
        with subprocess.Popen(
            ["mypy", f.name], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ) as proc:
            stdout, stderr = proc.communicate()
            assert not proc.returncode, "\n".join(
                [
                    "Non zero return code from mypy.",
                    "stderr:",
                    stderr.decode("utf-8") if stderr else "",
                    "stdout:",
                    stdout.decode("utf-8") if stdout else "",
                ]
            )

            assert (
                stdout.decode("utf-8") == "Success: no issues found in 1 source file\n"
            )
