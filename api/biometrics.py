# api/biometrics.py
# Règles métier — âge, taille, poids et IMC (profil utilisateur)

from __future__ import annotations

from typing import Optional

AGE_MIN = 18
AGE_MAX = 100
HEIGHT_CM_MIN = 90
HEIGHT_CM_MAX = 230
WEIGHT_KG_MIN = 20
WEIGHT_KG_MAX = 300
BMI_MIN = 10
BMI_MAX = 80


def compute_bmi(weight_kg: float, height_cm: float) -> float:
    """IMC = poids(kg) / taille(m)², arrondi à 2 décimales."""
    height_m = height_cm / 100
    return round(weight_kg / (height_m * height_m), 2)


def validate_age(age: Optional[int]) -> Optional[str]:
    if age is None:
        return None
    if age < AGE_MIN or age > AGE_MAX:
        return f"L'âge doit être compris entre {AGE_MIN} et {AGE_MAX} ans."
    return None


def validate_weight_kg(weight_kg: Optional[float]) -> Optional[str]:
    if weight_kg is None:
        return None
    if weight_kg < WEIGHT_KG_MIN or weight_kg > WEIGHT_KG_MAX:
        return f"Le poids doit être compris entre {WEIGHT_KG_MIN} et {WEIGHT_KG_MAX} kg."
    return None


def validate_height_cm(height_cm: Optional[float]) -> Optional[str]:
    if height_cm is None:
        return None
    if height_cm < HEIGHT_CM_MIN or height_cm > HEIGHT_CM_MAX:
        return (
            f"La taille doit être comprise entre {HEIGHT_CM_MIN} et {HEIGHT_CM_MAX} cm."
        )
    return None


def validate_bmi_value(bmi: float) -> Optional[str]:
    if bmi < BMI_MIN or bmi > BMI_MAX:
        return (
            f"L'IMC doit être compris entre {BMI_MIN} et {BMI_MAX} "
            f"(valeur calculée : {bmi})."
        )
    return None


def validate_bmi_from_metrics(
    weight_kg: Optional[float],
    height_cm: Optional[float],
) -> Optional[str]:
    """Valide l'IMC dérivé du poids et de la taille lorsque les deux sont renseignés."""
    if weight_kg is None or height_cm is None:
        return None
    return validate_bmi_value(compute_bmi(weight_kg, height_cm))


def collect_profile_issues(
    *,
    age: Optional[int] = None,
    weight_kg: Optional[float] = None,
    height_cm: Optional[float] = None,
    bmi: Optional[float] = None,
) -> list[str]:
    """Liste les problèmes biométriques sans lever d'exception (lecture / données legacy)."""
    issues: list[str] = []
    for check in (
        validate_age(age),
        validate_weight_kg(weight_kg),
        validate_height_cm(height_cm),
        validate_bmi_from_metrics(weight_kg, height_cm),
    ):
        if check:
            issues.append(check)

    if bmi is not None and weight_kg is not None and height_cm is not None:
        expected = compute_bmi(weight_kg, height_cm)
        if abs(bmi - expected) > 0.05:
            issues.append(
                "L'IMC enregistré ne correspond pas au poids et à la taille ; "
                "il sera recalculé à la prochaine mise à jour."
            )
        else:
            err = validate_bmi_value(bmi)
            if err:
                issues.append(err)

    return issues


def validate_user_biometrics(
    *,
    age: Optional[int] = None,
    weight_kg: Optional[float] = None,
    height_cm: Optional[float] = None,
    bmi: Optional[float] = None,
) -> Optional[str]:
    """Retourne le premier message d'erreur métier, ou None si tout est valide."""
    for check in (
        validate_age(age),
        validate_weight_kg(weight_kg),
        validate_height_cm(height_cm),
        validate_bmi_from_metrics(weight_kg, height_cm),
    ):
        if check:
            return check

    if bmi is not None and weight_kg is not None and height_cm is not None:
        expected = compute_bmi(weight_kg, height_cm)
        if abs(bmi - expected) > 0.05:
            return (
                "L'IMC ne peut pas être fourni manuellement : "
                "il est calculé automatiquement à partir du poids et de la taille."
            )
        err = validate_bmi_value(bmi)
        if err:
            return err

    return None


def resolve_bmi(
    weight_kg: Optional[float],
    height_cm: Optional[float],
) -> Optional[float]:
    """Calcule l'IMC si poids et taille sont présents, sinon None."""
    if weight_kg is None or height_cm is None:
        return None
    return compute_bmi(weight_kg, height_cm)
