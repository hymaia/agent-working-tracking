"""Unit tests for analysis utilities."""

from pathlib import Path

from agent_tracking.analysis import analyze_file, ClassInfo


SAMPLE_CODE = """
class Animal:
    def eat(self):
        pass

class Dog(Animal):
    def bark(self):
        pass
"""


def test_analyze_file(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.py"
    file_path.write_text(SAMPLE_CODE)

    classes = analyze_file(file_path)
    assert "Animal" in classes
    assert "Dog" in classes

    animal = classes["Animal"]
    assert isinstance(animal, ClassInfo)
    assert animal.methods == ["eat"]

    dog = classes["Dog"]
    assert dog.bases == ["Animal"]
    assert dog.methods == ["bark"]
