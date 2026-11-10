from app.auth.schemas import Consents, MeOut, ProfileOut
from app.models.user import User


def me_out(user: User) -> MeOut:
    p = user.profile
    return MeOut(
        id=user.id,
        email=user.email,
        role=user.role,
        created_at=user.created_at,
        profile=ProfileOut(display_name=p.display_name, education_level=p.education_level, target_roles=list(p.target_roles or [])),
        consents=Consents(voice_transcript=p.consent_voice_transcript, analytics=p.consent_analytics),
    )
