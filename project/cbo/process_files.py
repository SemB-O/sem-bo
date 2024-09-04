from .models import Procedure, Occupation, Record, Cid, ProcedureHasCid, ProcedureHasOccupation, ProcedureHasRecord
from .models.description import Description
from django.utils import timezone

class DataImporter:
    def __init__(self, encoding='iso-8859-1'):
        self.encoding = encoding

    def import_procedure_data(file):
        content = file.read()
        content_str = content.decode('iso-8859-1')

        for linha in content_str.split('\n'):
            co_procedimento = linha[0:10].strip() if len(linha) >= 10 else ''
            no_procedimento = linha[10:260].strip() if len(linha) >= 260 else ''
            tp_complexidade = linha[260].strip() if len(linha) >= 260 else ''
            tp_sexo = linha[261].strip() if len(linha) >= 261 else ''
            qt_maxima_execucao = int(linha[262:266].strip()) if len(linha) >= 266 else 0
            qt_dias_permanencia = int(linha[267:270].strip()) if len(linha) >= 270 else 0
            qt_pontos = int(linha[271:274].strip()) if len(linha) >= 274 else 0
            vl_idade_minima = int(linha[275:278].strip()) if len(linha) >= 278 else 0
            vl_idade_maxima = int(linha[279:282].strip()) if len(linha) >= 282 else 0
            vl_sh = int(linha[283:292].strip()) if len(linha) >= 292 else 0
            vl_sa = int(linha[293:302].strip()) if len(linha) >= 302 else 0
            vl_sp = int(linha[303:312].strip()) if len(linha) >= 312 else 0
            qt_tempo_permanencia = int(linha[320:324].strip()) if len(linha) >= 324 else 0
            dt_competencia = linha[324:330].strip() if len(linha) >= 330 else ''
            created_at = timezone.now()

            procedure, created = Procedure.objects.get_or_create(
                procedure_code=co_procedimento,
                defaults={
                    'name': no_procedimento,
                    'complexity_type': tp_complexidade,
                    'sex_type': tp_sexo,
                    'maximum_execution_amount': qt_maxima_execucao,
                    'stay_day_number': qt_dias_permanencia,
                    'points_number': qt_pontos,
                    'minimum_age_value': vl_idade_minima,
                    'maximum_age_value': vl_idade_maxima,
                    'SH_value': vl_sh,
                    'SA_value': vl_sa,
                    'SP_value': vl_sp,
                    'stay_time_number': qt_tempo_permanencia,
                    'competence_date': dt_competencia,
                    'created_at': created_at
                }
            )

            if not created:
                procedure.name = no_procedimento
                procedure.complexity_type = tp_complexidade
                procedure.sex_type = tp_sexo
                procedure.maximum_execution_amount = qt_maxima_execucao
                procedure.stay_day_number = qt_dias_permanencia
                procedure.points_number = qt_pontos
                procedure.minimum_age_value = vl_idade_minima
                procedure.maximum_age_value = vl_idade_maxima
                procedure.SH_value = vl_sh
                procedure.SA_value = vl_sa
                procedure.SP_value = vl_sp
                procedure.stay_time_number = qt_tempo_permanencia
                procedure.competence_date = dt_competencia
                procedure.created_at = created_at

            procedure.save()

    def import_occupation_data(file):
        content = file.read()
        content_str = content.decode('iso-8859-1')

        for linha in content_str.split('\n'):
            if len(linha) >= 6:
                co_ocupacao = linha[0:6].strip()
            else:
                co_ocupacao = ''

            if len(linha) >= 156:
                no_ocupacao = linha[6:156].strip()
            else:
                no_ocupacao = ''

            occupation, created = Occupation.objects.get_or_create(
                occupation_code=co_ocupacao,
                defaults={
                    'name': no_ocupacao,
                }
            )

            if not created:
                occupation.name = no_ocupacao

            occupation.save()

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

    def import_cid_data(file):
        content = file.read()
        content_str = content.decode('iso-8859-1')

        for linha in content_str.split('\n'):
            if len(linha) >= 4:
                co_cid = linha[0:4].strip()
            else:
                co_cid = ''

            if len(linha) >= 104:
                no_cid = linha[4:104].strip()
            else:
                no_cid = ''

            if len(linha) >= 105:
                tp_agravo = linha[104:105].strip()
            else:
                tp_agravo = ''

            if len(linha) >= 106:
                tp_sexo = linha[105:106].strip()
            else:
                tp_sexo = ''

            if len(linha) >= 107:
                tp_estadio = linha[106:107].strip()
            else:
                tp_estadio = ''

            if len(linha) >= 111:
                vl_campos_irradiados = int(linha[110:114].strip())
            else:
                vl_campos_irradiados = 0

            cid, created = Cid.objects.get_or_create(
                cid_code=co_cid,
                defaults={
                    'name': no_cid,
                    'grievance_type': tp_agravo,
                    'sex_type': tp_sexo,
                    'stadium_stype': tp_estadio,
                    'irradiated_fields_value': vl_campos_irradiados,
                }
            )

            if not created:
                cid.name = no_cid
                cid.grievance_type = tp_agravo
                cid.sex_type = tp_sexo
                cid.stadium_stype = tp_estadio
                cid.irradiated_fields_value = vl_campos_irradiados

            cid.save()

    def import_procedure_has_cid_data(file):
        content = file.read()
        content_str = content.decode('iso-8859-1')
        for linha in content_str.split('\n'):
            co_procedimento = linha[0:10].strip()
            co_cid = linha[10:14].strip()
            st_principal = linha[14:15].strip()
            dt_competencia = linha[15:21].strip()

            if not all([co_procedimento, co_cid, st_principal, dt_competencia]):
                continue

            procedure, created = Procedure.objects.get_or_create(
                procedure_code=co_procedimento,
            )

            cid, created = Cid.objects.get_or_create(
                cid_code=co_cid,
            )

            procedure_has_cid = ProcedureHasCid(
                st_principal=st_principal,
                competence_date=dt_competencia,
                procedure=procedure,
                cid=cid
            )
            procedure_has_cid.save()

    def import_procedure_has_occupation_data(file):
        content = file.read()
        content_str = content.decode('iso-8859-1')
        for linha in content_str.split('\n'):
            co_procedimento = linha[0:10].strip()
            co_ocupacao = linha[10:16].strip()
            dt_competencia = linha[16:22].strip()

            if not all([co_procedimento, co_ocupacao, dt_competencia]):
                continue

            if len(co_procedimento) > 10:
                co_procedimento = co_procedimento[:10]

            if len(co_ocupacao) > 6:
                co_ocupacao = co_ocupacao[:6]

            procedure, created = Procedure.objects.get_or_create(
                procedure_code=co_procedimento,
            )

            occupation, created = Occupation.objects.get_or_create(
                occupation_code=co_ocupacao,
            )

            procedure_has_occupation = ProcedureHasOccupation(
                competence_date=dt_competencia,
                procedure=procedure,
                occupation=occupation
            )
            procedure_has_occupation.save()

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
