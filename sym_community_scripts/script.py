from termcolor import cprint


class Script:
    def _section_start(self, text):
        cprint(f"\n{text}\n", "white", attrs=["bold"])

    def _section_end(self, text):
        cprint(f"{text}\n", "cyan")

    def _success(self, text):
        cprint(text, "green", attrs=["dark"])

    def _failure(self, text):
        cprint(text, "red", attrs=["dark"])

    def _error(self, text):
        cprint(f"\n{text}", "red")
