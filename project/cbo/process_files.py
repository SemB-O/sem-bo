import logging
from .models import Procedure, Occupation, Record, Cid, ProcedureHasCid, ProcedureHasOccupation, ProcedureHasRecord
from .models.description import Description
from django.utils import timezone
from django.db import transaction

logger = logging.getLogger(__name__)


class DataImporter:
    def __init__(self, encoding='iso-8859-1'):
        self.encoding = encoding

    @transaction.atomic
    @staticmethod
    def import_procedure_data(file):
        try:
            logger.info("Starting import of procedure data.")

            file_content = file.read()
            decoded_content = file_content.decode('iso-8859-1')
            logger.debug("File decoded successfully.")

            procedure_data = {}

            for index, line in enumerate(decoded_content.split('\n'), start=1):
                if not line.strip():
                    logger.debug(f"Line {index} is empty, skipping.")
                    continue

                co_procedimento = line[0:10].strip() if len(line) >= 10 else ''
                if not co_procedimento:
                    logger.warning(f"Line {index} missing procedure code, skipping: {line}")
                    continue

                procedure_data[co_procedimento] = {
                    'name': line[10:260].strip() if len(line) >= 260 else '',
                    'complexity_type': line[260].strip() if len(line) >= 260 else '',
                    'sex_type': line[261].strip() if len(line) >= 261 else '',
                    'maximum_execution_amount': int(line[262:266].strip()) if len(line) >= 266 else 0,
                    'stay_day_number': int(line[267:270].strip()) if len(line) >= 270 else 0,
                    'points_number': int(line[271:274].strip()) if len(line) >= 274 else 0,
                    'minimum_age_value': int(line[275:278].strip()) if len(line) >= 278 else 0,
                    'maximum_age_value': int(line[279:282].strip()) if len(line) >= 282 else 0,
                    'SH_value': int(line[283:292].strip()) if len(line) >= 292 else 0,
                    'SA_value': int(line[293:302].strip()) if len(line) >= 302 else 0,
                    'SP_value': int(line[303:312].strip()) if len(line) >= 312 else 0,
                    'stay_time_number': int(line[320:324].strip()) if len(line) >= 324 else 0,
                    'competence_date': line[324:330].strip() if len(line) >= 330 else '',
                    'created_at': timezone.now()
                }

            logger.info(f"Parsed {len(procedure_data)} procedures from file.")

            existing_procedures = Procedure.objects.filter(
                procedure_code__in=procedure_data.keys()
            )
            logger.info(f"Found {existing_procedures.count()} existing procedures in database.")

            to_update = []
            existing_codes = set()

            for procedure in existing_procedures:
                existing_codes.add(procedure.procedure_code)
                data = procedure_data[procedure.procedure_code]

                updated = False
                for field, value in data.items():
                    if getattr(procedure, field) != value:
                        setattr(procedure, field, value)
                        updated = True

                if updated:
                    to_update.append(procedure)

            to_create = [
                Procedure(procedure_code=code, **data)
                for code, data in procedure_data.items()
                if code not in existing_codes
            ]

            if to_create:
                Procedure.objects.bulk_create(to_create, batch_size=500)
                logger.info(f"Created {len(to_create)} new procedures.")

            if to_update:
                fields_to_update = list(procedure_data[next(iter(procedure_data))].keys())
                Procedure.objects.bulk_update(to_update, fields_to_update, batch_size=500)
                logger.info(f"Updated {len(to_update)} existing procedures.")

            logger.info("Procedure import completed successfully.")

        except Exception as e:
            logger.exception(f"Error during procedure data import: {str(e)}")
            raise

    @transaction.atomic
    @staticmethod
    def import_occupation_data(file):
        try:
            logger.info("Starting import of occupation data.")

            file_content = file.read()
            decoded_content = file_content.decode('iso-8859-1')
            logger.debug("File decoded successfully.")

            occupation_data = {}

            for index, line in enumerate(decoded_content.split('\n'), start=1):
                if not line.strip():
                    logger.debug(f"Line {index} is empty, skipping.")
                    continue

                co_ocupacao = line[0:6].strip() if len(line) >= 6 else ''
                no_ocupacao = line[6:156].strip() if len(line) >= 156 else ''

                if not co_ocupacao:
                    logger.warning(f"Line {index} missing occupation code, skipping: {line}")
                    continue

                occupation_data[co_ocupacao] = no_ocupacao

            logger.info(f"Parsed {len(occupation_data)} occupation entries from file.")

            existing_occupations = Occupation.objects.filter(
                occupation_code__in=occupation_data.keys()
            )
            logger.info(f"Found {existing_occupations.count()} existing occupations in database.")

            to_update = []
            existing_codes = set()

            for occupation in existing_occupations:
                existing_codes.add(occupation.occupation_code)
                new_name = occupation_data[occupation.occupation_code]
                if occupation.name != new_name and new_name:
                    occupation.name = new_name
                    to_update.append(occupation)

            to_create = [
                Occupation(occupation_code=code, name=name)
                for code, name in occupation_data.items()
                if code not in existing_codes
            ]

            if to_create:
                Occupation.objects.bulk_create(to_create, batch_size=500)
                logger.info(f"Created {len(to_create)} new occupations.")

            if to_update:
                Occupation.objects.bulk_update(to_update, ['name'], batch_size=500)
                logger.info(f"Updated {len(to_update)} existing occupations.")

            logger.info("Occupation import completed successfully.")

        except Exception as e:
            logger.exception(f"Error during occupation data import: {str(e)}")
            raise

    def import_record_data(file):
        content = file.read()
        content_str = content.decode('iso-8859-1')

        for linha in content_str.split('\n'):
            if len(linha) >= 2:
                co_registro = linha[0:2].strip()
            else:
                co_registro = ''

            if len(linha) >= 52:
                no_registro = linha[2:52].strip()
            else:
                no_registro = ''

            if len(linha) >= 58:
                dt_competencia = linha[52:58].strip()
            else:
                dt_competencia = ''

            record, created = Record.objects.get_or_create(
                record_code=co_registro,
                defaults={
                    'name': no_registro,
                    'competence_date': dt_competencia,
                }
            )

            if not created:
                record.name = no_registro
                record.competence_date = dt_competencia

            record.save()

    @transaction.atomic
    @staticmethod
    def import_cid_data(file):
        try:
            logger.info("Starting import of CID data.")

            file_content = file.read()
            decoded_content = file_content.decode('iso-8859-1')
            logger.debug("File decoded successfully.")

            cid_data = {}

            for idx, line in enumerate(decoded_content.split('\n'), start=1):
                if not line.strip():
                    logger.debug(f"Line {idx} is empty, skipping.")
                    continue

                co_cid = line[0:4].strip() if len(line) >= 4 else ''
                if not co_cid:
                    logger.warning(f"Line {idx} missing CID code, skipping: {line}")
                    continue

                cid_data[co_cid] = {
                    'name': line[4:104].strip() if len(line) >= 104 else '',
                    'grievance_type': line[104:105].strip() if len(line) >= 105 else '',
                    'sex_type': line[105:106].strip() if len(line) >= 106 else '',
                    'stadium_stype': line[106:107].strip() if len(line) >= 107 else '',
                    'irradiated_fields_value': int(line[110:114].strip()) if len(line) >= 111 and line[110:114].strip().isdigit() else 0
                }

            logger.info(f"Parsed {len(cid_data)} CID entries from file.")

            existing_cids = Cid.objects.filter(
                cid_code__in=cid_data.keys()
            )
            logger.info(f"Found {existing_cids.count()} existing CIDs in database.")

            to_update = []
            existing_codes = set()

            for cid in existing_cids:
                existing_codes.add(cid.cid_code)
                data = cid_data[cid.cid_code]

                updated = False
                for field, value in data.items():
                    if getattr(cid, field) != value:
                        setattr(cid, field, value)
                        updated = True

                if updated:
                    to_update.append(cid)

            to_create = [
                Cid(cid_code=code, **data)
                for code, data in cid_data.items()
                if code not in existing_codes
            ]

            if to_create:
                Cid.objects.bulk_create(to_create, batch_size=500)
                logger.info(f"Created {len(to_create)} new CIDs.")

            if to_update:
                fields_to_update = list(cid_data[next(iter(cid_data))].keys())
                Cid.objects.bulk_update(to_update, fields_to_update, batch_size=500)
                logger.info(f"Updated {len(to_update)} existing CIDs.")

            logger.info("CID import completed successfully.")

        except Exception as e:
            logger.exception(f"Error during CID data import: {str(e)}")
            raise

    @transaction.atomic
    @staticmethod
    def import_procedure_has_cid_data(file):
        try:
            logger.info("Starting import of procedure has CID data.")

            file_content = file.read()
            decoded_content = file_content.decode('iso-8859-1')
            logger.debug("File decoded successfully.")

            procedure_code_set = set()
            cid_code_set = set()
            relationship_data_set = set()

            for idx, line in enumerate(decoded_content.split('\n'), start=1):
                if not line.strip():
                    logger.debug(f"Line {idx} is empty, skipping.")
                    continue

                co_procedimento = line[0:10].strip()
                co_cid = line[10:14].strip()
                st_principal = line[14:15].strip()
                dt_competencia = line[15:21].strip()

                if not all([co_procedimento, co_cid, st_principal, dt_competencia]):
                    logger.warning(f"Line {idx} contains incomplete data, skipping: {line}")
                    continue

                procedure_code_set.add(co_procedimento)
                cid_code_set.add(co_cid)
                relationship_data_set.add((co_procedimento, co_cid, st_principal, dt_competencia))

            logger.info(f"Found {len(procedure_code_set)} unique procedures.")
            logger.info(f"Found {len(cid_code_set)} unique CIDs.")
            logger.info(f"Prepared to import {len(relationship_data_set)} relationships.")

            existing_procedures = Procedure.objects.filter(procedure_code__in=procedure_code_set)
            procedure_map = {proc.procedure_code: proc for proc in existing_procedures}

            existing_cids = Cid.objects.filter(cid_code__in=cid_code_set)
            cid_map = {cid.cid_code: cid for cid in existing_cids}

            logger.info(f"Found {len(procedure_map)} existing procedures in database.")
            logger.info(f"Found {len(cid_map)} existing CIDs in database.")

            missing_procedure_codes = procedure_code_set - procedure_map.keys()
            new_procedures = [Procedure(procedure_code=code) for code in missing_procedure_codes]
            if new_procedures:
                Procedure.objects.bulk_create(new_procedures, batch_size=500)
                logger.info(f"Created {len(new_procedures)} new procedures.")

            all_procedures = Procedure.objects.filter(procedure_code__in=procedure_code_set)
            procedure_map = {proc.procedure_code: proc for proc in all_procedures}

            missing_cid_codes = cid_code_set - cid_map.keys()
            new_cids = [Cid(cid_code=code) for code in missing_cid_codes]
            if new_cids:
                Cid.objects.bulk_create(new_cids, batch_size=500)
                logger.info(f"Created {len(new_cids)} new CIDs.")

            all_cids = Cid.objects.filter(cid_code__in=cid_code_set)
            cid_map = {cid.cid_code: cid for cid in all_cids}

            new_relationships = []
            for co_procedimento, co_cid, st_principal, dt_competencia in relationship_data_set:
                procedure = procedure_map.get(co_procedimento)
                cid = cid_map.get(co_cid)

                if procedure and cid:
                    new_relationships.append(
                        ProcedureHasCid(
                            st_principal=st_principal,
                            competence_date=dt_competencia,
                            procedure=procedure,
                            cid=cid
                        )
                    )
                else:
                    logger.warning(f"Procedure or CID not found for relationship: {co_procedimento}, {co_cid}")

            if new_relationships:
                ProcedureHasCid.objects.bulk_create(new_relationships, batch_size=500)
                logger.info(f"Inserted {len(new_relationships)} procedure-CID relationships.")

            logger.info("ProcedureHasCid import completed successfully.")

        except Exception as e:
            logger.exception(f"Error during procedure has CID data import: {str(e)}")
            raise

    @transaction.atomic
    @staticmethod
    def import_procedure_has_occupation_data(file):
        try:
            logger.info("Starting import of procedure and occupation data.")

            file_content = file.read()
            decoded_content = file_content.decode('iso-8859-1')
            logger.debug("File decoded successfully.")

            procedure_code_set = set()
            occupation_code_set = set()
            relationship_data_set = set()

            for idx, line in enumerate(decoded_content.split('\n'), start=1):
                if not line.strip():
                    logger.debug(f"Line {idx} is empty, skipping.")
                    continue

                procedure_code = line[0:10].strip()[:10]
                occupation_code = line[10:16].strip()[:6]
                competence_date = line[16:22].strip()

                if not all([procedure_code, occupation_code, competence_date]):
                    logger.warning(f"Line {idx} contains incomplete data, skipping: {line}")
                    continue

                procedure_code_set.add(procedure_code)
                occupation_code_set.add(occupation_code)
                relationship_data_set.add((procedure_code, occupation_code, competence_date))

            logger.info(f"Found {len(procedure_code_set)} unique procedures.")
            new_procedures = [Procedure(procedure_code=code) for code in procedure_code_set]
            Procedure.objects.bulk_create(new_procedures, batch_size=500, ignore_conflicts=True)
            logger.info("Procedures successfully inserted.")

            new_occupations = [Occupation(occupation_code=code) for code in occupation_code_set]
            logger.info(f"Found {len(occupation_code_set)} unique occupations.")
            Occupation.objects.bulk_create(new_occupations, batch_size=500, ignore_conflicts=True)
            logger.info("Occupations successfully inserted.")

            logger.info(f"Prepared to import {len(relationship_data_set)} relationships.")
            new_relationships = [
                ProcedureHasOccupation(
                    competence_date=competence_date,
                    procedure_id=procedure_code,
                    occupation_id=occupation_code
                )
                for procedure_code, occupation_code, competence_date in relationship_data_set
            ]
            ProcedureHasOccupation.objects.bulk_create(new_relationships, batch_size=500,)
            logger.info("Relationships successfully inserted.")

        except Exception as e:
            logger.exception(f"Error during data import: {str(e)}")
            raise

    def import_procedure_has_record_data(file):
        content = file.read()
        content_str = content.decode('iso-8859-1')
        for linha in content_str.split('\n'):
            co_procedimento = linha[0:10].strip()
            co_registro = linha[10:12].strip()
            dt_competencia = linha[12:18].strip()

            if not all([co_procedimento, co_registro, dt_competencia]):
                continue

            if len(co_procedimento) > 10:
                co_procedimento = co_procedimento[:10]

            if len(co_registro) > 2:
                co_registro = co_registro[:2]

            procedure, created = Procedure.objects.get_or_create(
                procedure_code=co_procedimento,
            )

            record, created = Record.objects.get_or_create(
                record_code=co_registro,
            )

            procedure_has_record = ProcedureHasRecord(
                competence_date=dt_competencia,
                procedure=procedure,
                record=record
            )
            procedure_has_record.save()     

    def import_description_data(file):
        content = file.read()
        content_str = content.decode('iso-8859-1')

        for linha in content_str.split('\n'):
            if len(linha) >= 4016:
                co_procedimento = linha[0:10].strip()
                description = linha[10:4010].strip()
                dt_competencia = linha[4011:4017].strip()

                procedure = Procedure.objects.filter(procedure_code=co_procedimento).first()
                if procedure:
                    description_obj, created = Description.objects.get_or_create(
                        procedure=procedure,
                        defaults={
                            'description': description,
                            'competence_date': dt_competencia,
                        }
                    )

                    if not created:
                        description_obj.description = description
                        description_obj.competence_date = dt_competencia

                    description_obj.save()   
