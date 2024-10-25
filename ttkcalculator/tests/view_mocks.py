""" Mocks of important interfaces from ttkcalculator.view module """

from dataclasses import dataclass, field

from ttkcalculator.view import Key, KeyCode


@dataclass
class DummyDisplay:
    _max_items: int
    update_history: list[str] = field(default_factory=list)

    @property
    def tk_variable(self) -> None:
        return None

    def update(self, text: str) -> None:
        self.update_history.append(text)

    @property
    def max_items(self) -> int:
        return self._max_items


@dataclass()
class DummyKeypad:
    press_history: list[str] = field(default_factory=list)
    release_history: int = 0

    def register(self, key: Key) -> None:
        pass

    def press(self, code: KeyCode) -> None:
        self.press_history.append(code)

    def release_all(self) -> None:
        self.release_history += 1

