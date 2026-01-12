import logging
from .models import Procedure, Occupation, Record, Cid, ProcedureHasCid, ProcedureHasOccupation, ProcedureHasRecord, Competence
from .models.descricao import Description
from django.utils import timezone
from django.db import transaction

logger = logging.getLogger(__name__)


def safe_int(value, default=0):
    """Converte string para int de forma segura, retornando default se vazio ou inválido"""
    if value is None:
        return default
    if isinstance(value, int):
        return value
    if not value or not str(value).strip():
        return default
    try:
        return int(str(value).strip())
    except (ValueError, AttributeError, TypeError):
        return default


class DataImporter:
    def __init__(self, encoding='iso-8859-1', allow_overwrite=False):
        self.encoding = encoding
        self.allow_overwrite = allow_overwrite
        self._warned_competences = set()  # Para evitar warnings repetidos
    
    def check_competence_conflict(self, new_competence_code):
        """
        Verifica se há conflito de competência antes de importar.
        Retorna True se pode prosseguir, False se deve abortar.
        """
        if not new_competence_code or new_competence_code.endswith('9999'):
            # Competências atemporais podem ser atualizadas sempre
            return True
        
        # Verifica se já existe no banco
        existing = Competence.objects.filter(
            code=new_competence_code,
            is_atemporal=False
        ).exists()
        
        if existing:
            if self.allow_overwrite:
                # Avisa apenas uma vez por competência
                if new_competence_code not in self._warned_competences:
                    logger.warning(
                        f"Competência {new_competence_code} já existe. "
                        f"Sobrescrevendo conforme allow_overwrite=True"
                    )
                    self._warned_competences.add(new_competence_code)
                return True
            else:
                logger.error(
                    f"BLOQUEADO: Tentativa de sobrescrever competência {new_competence_code} "
                    f"que já existe no banco. Use allow_overwrite=True para forçar."
                )
                return False
        
        return True

    @transaction.atomic
    def import_procedure_data(self, file):
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
                    'maximum_execution_amount': safe_int(line[262:266]),
                    'stay_day_number': safe_int(line[267:270]),
                    'points_number': safe_int(line[271:274]),
                    'minimum_age_value': safe_int(line[275:278]),
                    'maximum_age_value': safe_int(line[279:282]),
                    'SH_value': safe_int(line[283:292]),
                    'SA_value': safe_int(line[293:302]),
                    'SP_value': safe_int(line[303:312]),
                    'stay_time_number': safe_int(line[320:324]),
                    'competence_date': line[324:330].strip() if len(line) >= 330 else '',
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
    def import_occupation_data(self, file):
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

    def import_record_data(self, file):
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
    def import_cid_data(self, file):
        try:
            logger.info("Starting import of CID data.")

            file_content = file.read()
            decoded_content = file_content.decode('iso-8859-1')
            logger.debug("File decoded successfully.")

            cid_data = {}

            for index, line in enumerate(decoded_content.split('\n'), start=1):
                if not line.strip():
                    logger.debug(f"Line {index} is empty, skipping.")
                    continue

                co_cid = line[0:4].strip() if len(line) >= 4 else ''
                if not co_cid:
                    logger.warning(f"Line {index} missing CID code, skipping: {line}")
                    continue

                # Garantir que irradiated_fields_value seja sempre um inteiro válido
                irradiated_value = safe_int(line[110:114] if len(line) >= 114 else '', 0)
                if irradiated_value is None:
                    logger.warning(f"Line {index}: irradiated_fields_value is None for CID {co_cid}, setting to 0")
                    irradiated_value = 0

                cid_data[co_cid] = {
                    'name': line[4:104].strip() if len(line) >= 104 else '',
                    'grievance_type': line[104:105].strip() if len(line) >= 105 else '',
                    'sex_type': line[105:106].strip() if len(line) >= 106 else '',
                    'stadium_stype': line[106:107].strip() if len(line) >= 107 else '',
                    'irradiated_fields_value': irradiated_value
                }

            logger.info(f"Parsed {len(cid_data)} CID entries from file.")
            
            # Verificar se há valores None no dicionário
            for code, data in cid_data.items():
                if data['irradiated_fields_value'] is None:
                    logger.error(f"CID {code} has None irradiated_fields_value! Fixing to 0")
                    data['irradiated_fields_value'] = 0

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
                    # Garantir que irradiated_fields_value nunca seja None
                    if field == 'irradiated_fields_value' and value is None:
                        value = 0
                    if getattr(cid, field) != value:
                        setattr(cid, field, value)
                        updated = True

                if updated:
                    to_update.append(cid)

            to_create = [
                Cid(
                    cid_code=code,
                    name=data['name'],
                    grievance_type=data['grievance_type'],
                    sex_type=data['sex_type'],
                    stadium_stype=data['stadium_stype'],
                    irradiated_fields_value=data['irradiated_fields_value'] if data['irradiated_fields_value'] is not None else 0
                )
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
    def import_procedure_has_cid_data(self, file):
        try:
            logger.info("Starting import of procedure has CID data.")

            file_content = file.read()
            decoded_content = file_content.decode('iso-8859-1')
            logger.debug("File decoded successfully.")

            procedure_code_set = set()
            cid_code_set = set()
            relationship_data_set = set()

            for index, line in enumerate(decoded_content.split('\n'), start=1):
                if not line.strip():
                    logger.debug(f"Line {index} is empty, skipping.")
                    continue

                co_procedimento = line[0:10].strip()
                co_cid = line[10:14].strip()
                st_principal = line[14:15].strip()
                dt_competencia = line[15:21].strip()

                if not all([co_procedimento, co_cid, st_principal, dt_competencia]):
                    logger.warning(f"Line {index} contains incomplete data, skipping: {line}")
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
            new_cids = [
                Cid(
                    cid_code=code,
                    name='',
                    grievance_type='',
                    sex_type='',
                    stadium_stype='',
                    irradiated_fields_value=0
                )
                for code in missing_cid_codes
            ]
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
    def import_procedure_has_occupation_data(self, file):
        try:
            logger.info("Starting import of procedure and occupation data.")

            file_content = file.read()
            decoded_content = file_content.decode('iso-8859-1')
            logger.debug("File decoded successfully.")

            procedure_code_set = set()
            occupation_code_set = set()
            relationship_data_set = set()

            for index, line in enumerate(decoded_content.split('\n'), start=1):
                if not line.strip():
                    logger.debug(f"Line {index} is empty, skipping.")
                    continue

                procedure_code = line[0:10].strip()[:10]
                occupation_code = line[10:16].strip()[:6]
                competence_date = line[16:22].strip()

                if not all([procedure_code, occupation_code, competence_date]):
                    logger.warning(f"Line {index} contains incomplete data, skipping: {line}")
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

    @transaction.atomic
    def import_procedure_has_record_data(self, file):
        try:
            logger.info("Starting import of procedure has record data.")

            file_content = file.read()
            decoded_content = file_content.decode('iso-8859-1')
            logger.debug("File decoded successfully.")

            procedure_code_set = set()
            record_code_set = set()
            relationship_data_set = set()

            for index, line in enumerate(decoded_content.split('\n'), start=1):
                if not line.strip():
                    logger.debug(f"Line {index} is empty, skipping.")
                    continue

                co_procedimento = line[0:10].strip()
                co_registro = line[10:12].strip()
                dt_competencia = line[12:18].strip()

                if not all([co_procedimento, co_registro, dt_competencia]):
                    logger.warning(f"Line {index} contains incomplete data, skipping: {line}")
                    continue

                if len(co_procedimento) > 10:
                    co_procedimento = co_procedimento[:10]

                if len(co_registro) > 2:
                    co_registro = co_registro[:2]

                procedure_code_set.add(co_procedimento)
                record_code_set.add(co_registro)
                relationship_data_set.add((co_procedimento, co_registro, dt_competencia))

            logger.info(f"Found {len(procedure_code_set)} unique procedures.")
            logger.info(f"Found {len(record_code_set)} unique records.")
            logger.info(f"Prepared to import {len(relationship_data_set)} relationships.")

            existing_procedures = Procedure.objects.filter(procedure_code__in=procedure_code_set)
            procedure_map = {proc.procedure_code: proc for proc in existing_procedures}

            existing_records = Record.objects.filter(record_code__in=record_code_set)
            record_map = {rec.record_code: rec for rec in existing_records}

            logger.info(f"Found {len(procedure_map)} existing procedures.")
            logger.info(f"Found {len(record_map)} existing records.")

            missing_procedure_codes = procedure_code_set - procedure_map.keys()
            new_procedures = [Procedure(procedure_code=code) for code in missing_procedure_codes]
            if new_procedures:
                Procedure.objects.bulk_create(new_procedures, batch_size=500)
                logger.info(f"Created {len(new_procedures)} new procedures.")

            all_procedures = Procedure.objects.filter(procedure_code__in=procedure_code_set)
            procedure_map = {proc.procedure_code: proc for proc in all_procedures}

            missing_record_codes = record_code_set - record_map.keys()
            new_records = [Record(record_code=code) for code in missing_record_codes]
            if new_records:
                Record.objects.bulk_create(new_records, batch_size=500)
                logger.info(f"Created {len(new_records)} new records.")

            all_records = Record.objects.filter(record_code__in=record_code_set)
            record_map = {rec.record_code: rec for rec in all_records}

            new_relationships = []
            for co_procedimento, co_registro, dt_competencia in relationship_data_set:
                procedure = procedure_map.get(co_procedimento)
                record = record_map.get(co_registro)

                if procedure and record:
                    new_relationships.append(
                        ProcedureHasRecord(
                            competence_date=dt_competencia,
                            procedure=procedure,
                            record=record
                        )
                    )
                else:
                    logger.warning(f"Procedure or Record not found for relationship: {co_procedimento}, {co_registro}")

            if new_relationships:
                ProcedureHasRecord.objects.bulk_create(new_relationships, batch_size=500)
                logger.info(f"Inserted {len(new_relationships)} procedure-record relationships.")

            logger.info("ProcedureHasRecord import completed successfully.")

        except Exception as e:
            logger.exception(f"Error during procedure has record data import: {str(e)}")
            raise
    
    def import_description_data(self, file):
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

    @staticmethod
    @transaction.atomic
    def sync_competences():
        """
        Sincroniza a tabela de competências com base em todos os valores 
        de competence_date encontrados nas tabelas SIGTAP.
        """
        logger.info("Starting competence synchronization...")
        
        competence_codes = set()
        
        # Coleta competências de todas as tabelas que possuem o campo
        for model in [Procedure, Record, ProcedureHasCid, ProcedureHasRecord, Description]:
            codes = model.objects.values_list('competence_date', flat=True).distinct()
            competence_codes.update([code for code in codes if code])
        
        logger.info(f"Found {len(competence_codes)} unique competence codes")
        
        created_count = 0
        updated_count = 0
        
        for code in competence_codes:
            competence, created = Competence.objects.get_or_create(code=code)
            if created:
                created_count += 1
            else:
                # Re-salva para reprocessar (caso a lógica tenha mudado)
                competence.save()
                updated_count += 1
        
        logger.info(f"Competence sync complete: {created_count} created, {updated_count} updated")
        
        # Retorna estatísticas
        return {
            'total': len(competence_codes),
            'created': created_count,
            'updated': updated_count,
            'real_competences': Competence.objects.filter(is_atemporal=False).count(),
            'atemporal_competences': Competence.objects.filter(is_atemporal=True).count(),
        }
