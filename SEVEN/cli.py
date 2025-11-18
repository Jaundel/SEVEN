from time import sleep
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn
from rich.text import Text
from pyfiglet import Figlet

console = Console()

# ---- GENERATE ASCII USING PYFIGLET ---- #
fig = Figlet(font="banner3-D")  # you can try fonts like: 'block', 'big', 'slant', 'standard'  //contrast
ascii_project = fig.renderText("PROJECT")
ascii_seven = fig.renderText("SEVEN")

ASCII_LOGO = ascii_project + ascii_seven


# ---- GRADIENT FUNCTION ---- #
def gradient_text(text: str, color1: str, color2: str) -> Text:
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    start = hex_to_rgb(color1)
    end = hex_to_rgb(color2)

    result = Text()

    for line in text.splitlines(True):
        length = len(line)
        for i, char in enumerate(line):
            ratio = i / (length - 1) if length > 1 else 0
            r = int(start[0] + (end[0] - start[0]) * ratio)
            g = int(start[1] + (end[1] - start[1]) * ratio)
            b = int(start[2] + (end[2] - start[2]) * ratio)
            result.append(char, style=f"rgb({r},{g},{b})")

    return result


def print_gradient_logo():
    logo = gradient_text(ASCII_LOGO, "#6a00ff", "#00eaff")
    console.print(logo)


def typewriter(text: str, delay: float = 0.02, style="bold white"):
    for line in text.split("\n"):
        console.print(line, style=style)
        sleep(delay)


def loading_bar():
    with Progress(
        TextColumn("[bold cyan]Launching Project SEVEN..."),
        BarColumn(bar_width=None),
    ) as progress:
        task = progress.add_task("", total=100)
        for _ in range(100):
            sleep(0.01)
            progress.update(task, advance=1)


def main():
    console.clear()

    print_gradient_logo()

    typewriter(
        "Welcome to Project SEVEN — your personal local AI system.\n",
        delay=0.03,
        style="bold magenta"
    )

    typewriter(
        "AI Systems • Local Models • Agents • Automation\n",
        delay=0.03,
        style="bold cyan"
    )

    loading_bar()

    console.print("\n[bold green]System Ready.[/bold green]")
    console.print("[white]Type[/white] [bold cyan]help[/bold cyan] [white]to begin.[/white]\n")


if __name__ == "__main__":
    main()
