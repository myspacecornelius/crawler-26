"""
Pre-built outreach sequence templates for different verticals.
Variables use {{var_name}} syntax for personalization.
"""

from .base import EmailStep, OutreachSequence


def vc_intro_sequence() -> OutreachSequence:
    """3-step VC intro sequence for founders seeking funding."""
    return OutreachSequence(
        name="VC Intro Sequence",
        steps=[
            EmailStep(
                subject="Quick intro — {{sender_company}} x {{company}}",
                body="""Hi {{first_name}},

I came across {{company}} and your work in {{sectors}} — really impressive portfolio.

I'm {{sender_name}}, founder of {{sender_company}}. We're building {{sender_pitch}} and are currently raising our {{sender_stage}} round.

Given your focus on {{sectors}}, I thought there might be a fit. Would you have 15 minutes this week for a quick intro call?

Best,
{{sender_name}}
{{sender_company}}""",
                delay_days=0,
                step_number=1,
            ),
            EmailStep(
                subject="Re: Quick intro — {{sender_company}} x {{company}}",
                body="""Hi {{first_name}},

Just wanted to follow up on my note below. We recently {{sender_traction}} and I'd love to share more context.

Would {{meeting_time}} work for a brief call?

Best,
{{sender_name}}""",
                delay_days=3,
                step_number=2,
            ),
            EmailStep(
                subject="Re: Quick intro — {{sender_company}} x {{company}}",
                body="""Hi {{first_name}},

Last follow-up — I know inboxes get busy. If the timing isn't right, no worries at all.

If it helps, here's our deck: {{sender_deck_link}}

Happy to connect whenever it makes sense.

Best,
{{sender_name}}
{{sender_company}}""",
                delay_days=5,
                step_number=3,
            ),
        ],
    )


def pe_intro_sequence() -> OutreachSequence:
    """3-step PE intro sequence for deal sourcing."""
    return OutreachSequence(
        name="PE Deal Intro",
        steps=[
            EmailStep(
                subject="{{sender_company}} — potential fit for {{company}} portfolio",
                body="""Hi {{first_name}},

I'm reaching out because {{sender_company}} aligns closely with {{company}}'s investment thesis in {{sectors}}.

We're at {{sender_revenue}} in ARR with {{sender_growth}} YoY growth, and exploring strategic partnerships or growth capital.

Would you be open to a 20-minute conversation?

Best,
{{sender_name}}
{{sender_title}}, {{sender_company}}""",
                delay_days=0,
                step_number=1,
            ),
            EmailStep(
                subject="Re: {{sender_company}} — potential fit for {{company}} portfolio",
                body="""Hi {{first_name}},

Following up — wanted to share a quick snapshot:
- Revenue: {{sender_revenue}}
- Growth: {{sender_growth}} YoY
- Market: {{sender_market_size}}

Happy to send our CIM if there's interest.

Best,
{{sender_name}}""",
                delay_days=4,
                step_number=2,
            ),
            EmailStep(
                subject="Re: {{sender_company}} — potential fit",
                body="""Hi {{first_name}},

Final note — if the timing isn't right, I completely understand. Would it make sense to reconnect in Q{{next_quarter}}?

Best,
{{sender_name}}
{{sender_company}}""",
                delay_days=7,
                step_number=3,
            ),
        ],
    )


def family_office_sequence() -> OutreachSequence:
    """2-step family office intro — shorter and more discreet."""
    return OutreachSequence(
        name="Family Office Intro",
        steps=[
            EmailStep(
                subject="Direct investment opportunity — {{sender_company}}",
                body="""Hi {{first_name}},

I'm {{sender_name}} from {{sender_company}}. We're a {{sender_description}} currently exploring co-investment partnerships with select family offices.

Given {{company}}'s focus on {{sectors}}, I thought this might be relevant.

Happy to share a brief overview if you're open to it.

Best,
{{sender_name}}
{{sender_company}}""",
                delay_days=0,
                step_number=1,
            ),
            EmailStep(
                subject="Re: Direct investment opportunity — {{sender_company}}",
                body="""Hi {{first_name}},

Just a gentle follow-up. I know direct deals require careful consideration — happy to start with an informal conversation whenever convenient.

Best,
{{sender_name}}""",
                delay_days=5,
                step_number=2,
            ),
        ],
    )


def corp_dev_sequence() -> OutreachSequence:
    """2-step corporate development intro for M&A conversations."""
    return OutreachSequence(
        name="Corp Dev Intro",
        steps=[
            EmailStep(
                subject="Strategic fit — {{sender_company}} + {{company}}",
                body="""Hi {{first_name}},

I'm {{sender_name}}, {{sender_title}} at {{sender_company}}. We've been following {{company}}'s activity in {{sectors}} and see strong strategic alignment.

{{sender_company}} is {{sender_description}}, and I believe there's an interesting conversation to be had around potential collaboration or partnership.

Would you have time for a brief call this week?

Best,
{{sender_name}}
{{sender_company}}""",
                delay_days=0,
                step_number=1,
            ),
            EmailStep(
                subject="Re: Strategic fit — {{sender_company}} + {{company}}",
                body="""Hi {{first_name}},

Wanted to follow up briefly. If a call doesn't work right now, I'm happy to send over a one-pager on {{sender_company}} for your review.

Best,
{{sender_name}}""",
                delay_days=5,
                step_number=2,
            ),
        ],
    )


TEMPLATES = {
    "vc": vc_intro_sequence,
    "pe": pe_intro_sequence,
    "family_office": family_office_sequence,
    "corp_dev": corp_dev_sequence,
}


def get_template(vertical: str) -> OutreachSequence:
    """Get the default outreach template for a vertical."""
    factory = TEMPLATES.get(vertical)
    if not factory:
        raise ValueError(f"No template for vertical '{vertical}'. Available: {list(TEMPLATES.keys())}")
    return factory()
