"""Reglas para tratar datos personales por capa."""
from dataclasses import dataclass


# =============================================================================
@dataclass(frozen=True)
class PrivacyRule:
    """Define el tratamiento de un campo sensible.

    Attributes:
        layer_name: Capa del modelo.
        table_name: Tabla a la que aplica la regla.
        field_name: Campo revisado.
        classification: Tipo de sensibilidad.
        handling: Forma en que se trata el campo.
    """
    layer_name: str
    table_name: str
    field_name: str
    classification: str
    handling: str


# =============================================================================
def build_privacy_rules() -> list[PrivacyRule]:
    """Devuelve el inventario de reglas de privacidad.

    Returns:
        list[PrivacyRule]: Reglas por capa y campo.
    """
    return [
        PrivacyRule(
            layer_name="raw",
            table_name="raw.raw_citas_sur",
            field_name="documento_identidad",
            classification="confidencial",
            handling="Se conserva el valor original y se limita su uso a la capa raw.",
        ),
        PrivacyRule(
            layer_name="raw",
            table_name="raw.raw_citas_sur",
            field_name="telefono",
            classification="confidencial",
            handling="Se conserva el valor original y se limita su uso a la capa raw.",
        ),
        PrivacyRule(
            layer_name="raw",
            table_name="raw.raw_citas_norte",
            field_name="observaciones",
            classification="confidencial",
            handling="Se conserva en raw y no se publica en clean ni consumo.",
        ),
        PrivacyRule(
            layer_name="raw",
            table_name="raw.raw_citas_sur",
            field_name="observaciones",
            classification="confidencial",
            handling="Se conserva en raw y no se publica en clean ni consumo.",
        ),
        PrivacyRule(
            layer_name="raw",
            table_name="raw.raw_citas_occidente",
            field_name="observaciones",
            classification="confidencial",
            handling="Se conserva en raw y no se publica en clean ni consumo.",
        ),
        PrivacyRule(
            layer_name="raw",
            table_name="raw.raw_whatsapp_eventos",
            field_name="payload_raw",
            classification="confidencial",
            handling="Se conserva el JSON original solo en raw.",
        ),
        PrivacyRule(
            layer_name="clean",
            table_name="clean.clean_citas",
            field_name="paciente_sk",
            classification="privada",
            handling="Se usa una clave hash estable y no se expone el identificador fuente.",
        ),
        PrivacyRule(
            layer_name="clean",
            table_name="clean.clean_whatsapp_eventos",
            field_name="destinatario_hash",
            classification="privada",
            handling="Se expone solo el hash del teléfono para análisis.",
        ),
        PrivacyRule(
            layer_name="mart",
            table_name="mart.fact_citas",
            field_name="paciente_sk",
            classification="privada",
            handling="La capa de consumo usa solo identificadores seudonimizados.",
        )
    ]
