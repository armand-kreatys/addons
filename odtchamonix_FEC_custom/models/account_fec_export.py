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
            # Ajouter une nouvelle colonne "Analytique"
            header.append("Analytique")
            rows_to_write.append(header)

            for row in reader:
                journal_code = row[0]       # JournalCode
                compte_num = row[4]         # CompteNum
                compte_lib = row[5]         # CompteLib
                ecriture_lib = row[10]      # EcritureLib
                # PieceDate (date de la pièce comptable)
                piece_date = row[9]

                # *** Modifications dans la colonne "JournalCode" ***
                if journal_code == "CSCHX":
                    journal_code = "CECHX"
                elif journal_code == "CCD1":
                    journal_code = "CSCHX"
                row[0] = journal_code

                # *** Modifications dans la colonne "CompteNum" ***
                if compte_num == "4710000":
                    compte_num = "5111100"
                row[4] = compte_num

                # *** Modifications dans la colonne "CompteLib" ***
                if compte_lib == "Compte attente divers":
                    compte_lib = "Espèces à encaisser Chamonix"
                row[5] = compte_lib

                # Remplacements spécifiques basés sur des motifs
                if "Paiement manuel : Carte paiement Pdv" in ecriture_lib:
                    ecriture_lib = f"Paiement CB {piece_date}"
                elif "Paiement manuel : Chèques vacances paiement Pdv" in ecriture_lib:
                    ecriture_lib = f"Paiement ANCV {piece_date}"
                elif "Paiement manuel : Chèques paiement Pdv" in ecriture_lib:
                    ecriture_lib = f"Paiement CHQ {piece_date}"

                # *** Modifications dans la colonne "EcritureLib" ***
                if compte_num in ["4457150", "4457220", "7073500", "707100", "7078200", "7072300"]:
                    ecriture_lib = "CLIENT BOUTIQUE CHAMONIX"
                else:
                    ecriture_lib = ecriture_lib.replace("Carte", "CB")
                    ecriture_lib = ecriture_lib.replace(
                        "Chèques vacances", "ANCV")
                    ecriture_lib = ecriture_lib.replace("Chèques", "CHQ")
                    ecriture_lib = ecriture_lib.replace("Espèces", "ESP")

                row[10] = ecriture_lib

                # *** Ajout de la colonne analytique ***
                if compte_num.startswith("707"):
                    analytique = "ACCU250TA"
                elif compte_num == "7088100":
                    analytique = "ACCU260TA"
                elif compte_num == "7085100":
                    analytique = "ACCU265TA"
                elif compte_num == "7085200":
                    analytique = "ACCU265NT"
                else:
                    analytique = ""
                row.append(analytique)

                # Ajouter la ligne modifiée à la liste
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
