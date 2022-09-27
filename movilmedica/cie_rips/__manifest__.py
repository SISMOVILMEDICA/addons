{
    "name": "CIE RIPS",
    "summary": "TABLA DE LA CLASIFICACIÓN ESTADÍSTICA INTERNACIONAL DE ENFERMEDADES Y PROBLEMAS RELACIONADOS CON LA SALUD, DECIMA REVISIÓN (CIE-10) PARA EL REGISTRO INDIVIDUAL DE PRESTACIONES DE SERVICIOS (RIPS) CON RESTRICCIONES DE SEXO, EDAD Y CODIGOS QUE NO SON AFECCIÓN PRINCIPAL",
    "description": """
SIGLAS
======

SEXO
    * H= Válido solo para hombres
    * M= Válido solo para mujeres
    * A= Aplica para ambos sexos

EDAD
    * LIMITE INFERIOR= Se refiere a la edad mínima aceptada para que ocurra el evento por dicha causa
    * LIMITE SUPERIOR= Se refiere a la edad máxima aceptada para que ocurra el evento por dicha causa

Para la interpretación de los LIMITES, el primer dígito se refiere:
    * 1 a horas
    * 2 a días
    * 3 a meses
    * 4 a años

Los dos siguientes dígitos corresponde a la edad
    * 000 significa que no hay restricción en edad mínima
    * 599 que no hay restricción en edad máxima
    * 0 que no hay restricción en edad
""",
    "author": "Odone",
    "website": "https://www.odone.com.co/",
    "version": "1",
    # always loaded
    "data": [
        "data/cie_rips_data.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
}
