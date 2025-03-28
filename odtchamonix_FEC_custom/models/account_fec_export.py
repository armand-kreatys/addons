# -*- coding: utf-8 -*-
from odoo import models, fields, api
import csv
import io
import logging

_logger = logging.getLogger(__name__)


class CustomFecExportWizard(models.TransientModel):
    _inherit = 'l10n_fr.fec.export.wizard'

    def generate_fec(self):
        # Appel de la méthode originale pour générer les données initiales
        result = super(CustomFecExportWizard, self).generate_fec()
        _logger.info(
            "FEC file generation started. Processing generated content.")

        # Récupérer le contenu du fichier CSV généré
        content = result['file_content'].decode()
        rows_to_write = []

        # Lire le fichier CSV existant
        with io.StringIO(content) as fecfile:
            reader = csv.reader(fecfile, delimiter='|')
            header = next(reader)  # En-tête du fichier
            rows_to_write.append(header)

            for row in reader:
                compte_lib = row[5]  # CompteLib
                comp_aux_num = row[6]  # CompAuxNum

                _logger.info(
                    f"Processing row - CompteLib: '{compte_lib}', Original CompAuxNum: '{comp_aux_num}'")

                # Si CompAuxNum est déjà rempli, on ne fait rien
                if comp_aux_num.strip():
                    _logger.info(
                        f"CompAuxNum already filled: '{comp_aux_num}'. Skipping extraction.")
                    rows_to_write.append(row)
                    continue

                # Si CompAuxNum est vide et que CompteLib contient " / ", extraire la partie après " / "
                if not comp_aux_num.strip() and " / " in compte_lib:
                    try:
                        comp_aux_num = compte_lib.split(" / ", 1)[1].strip()
                        # Supprimer les virgules et nettoyer la valeur
                        comp_aux_num = comp_aux_num.replace(
                            ',', '').replace('.', '')
                        _logger.info(
                            f"Extracted and cleaned CompAuxNum from CompteLib: '{comp_aux_num}'")
                    except Exception as e:
                        _logger.error(
                            f"Error extracting CompAuxNum from CompteLib: {e}")
                        comp_aux_num = ""
                else:
                    _logger.info(
                        f"No extraction needed. Using original CompAuxNum: '{comp_aux_num}'")

                # Mettre à jour la colonne CompAuxNum
                row[6] = comp_aux_num
                rows_to_write.append(row)

        # Réécrire les données modifiées dans un nouveau fichier CSV
        with io.StringIO() as new_fecfile:
            writer = csv.writer(new_fecfile, delimiter='|',
                                lineterminator='\r\n')
            writer.writerows(rows_to_write)
            new_content = new_fecfile.getvalue().encode()

        _logger.info(
            "FEC file post-processing completed. New content generated.")

        # Mettre à jour le résultat avec le nouveau contenu
        result['file_content'] = new_content
        return result
