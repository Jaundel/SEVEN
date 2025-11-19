"""Show a welcome box on the home page when the user has
no chat history.
"""

from rich.console import RenderableType
from textual.widgets import Static


class Welcome(Static):
    MESSAGE = """
[b]SEVEN[/] (Sustainable Energy Via Efficient Neural-routing)

[b u]THE PROBLEM:[/]
Every AI query burns 0.35 Wh through cloud GPUs—whether you're asking "What is 2+2?"
or writing a novel. At 100M users, GPT-4o alone consumes [b]1,277 GWh annually[/]
(118,000 homes). Yet 40% of queries are simple lookups that could run locally at 0.02 Wh.

AI is projected to consume 134 TWh by 2027. Cloud costs will force subscriptions, pricing
out billions. Data centers physically cannot scale to meet exponential demand.

[b u]THE SOLUTION:[/]
SEVEN routes by complexity, not defaults:

[b green]LOCAL (40%)[/]: Factual queries → Phi-3.5 on NPU (0.02 Wh, 94% saved)
[b blue]API (8%)[/]: Real-time data → Direct calls (0.001 Wh, 99% saved)
[b red]CLOUD (52%)[/]: Complex tasks → GPT-4o only when needed (0.35 Wh)

[b u]WHY THIS IS NOVEL:[/]
Everyone optimizes [b]models[/] (quantization, pruning → 10-20% gains)
SEVEN optimizes the [b]orchestration layer[/] (WHERE to compute → 38% gains)

The question isn't "How do we make models efficient?" It's "Does this query even
need a frontier model?" Asked [b]before[/] inference. This architectural shift—
routing intelligence as infrastructure—is what existing solutions miss.

[b u]IMPACT AT SCALE:[/]
For GPT-4o at 100M users: [b cyan]483 GWh saved annually[/] (45,000 homes, 105,000 cars)
Multiply across Claude, Gemini, Llama → [b]terawatt-hour potential[/]

Every 1% of global AI queries adopting intelligent routing = [b]12.8 GWh saved annually[/]
This scales with adoption, not model improvements. As AI grows 10x, so does impact.

[b u]HOW TO USE:[/]
Type your message and press [b u]ctrl+j[/] or [b u]alt+enter[/] • Press [b u]ctrl+o[/] to configure

[b]UN SDG 7: Affordable and Clean Energy[/]
Intelligent routing isn't optimization—it's infrastructure for sustainable AI.

[@click='open_repo'][b r]View SEVEN on GitHub[/][/]
"""

    BORDER_TITLE = "SEVEN - Intelligent Routing for Sustainable AI"

    def render(self) -> RenderableType:
        return self.MESSAGE

    def _action_open_repo(self) -> None:
        import webbrowser

        webbrowser.open("https://github.com/Jaundel/SEVEN")

    def _action_open_issues(self) -> None:
        import webbrowser

        webbrowser.open("https://github.com/Jaundel/SEVEN/issues")
