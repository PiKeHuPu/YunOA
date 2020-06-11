import datetime
import json
import random

import xlrd
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.utils import timezone
from django.views import View

from exam.models import ExamType, ExamOneChoose, ExamMutiChoose, ExamMutiChooseAnswer, ExamTorF, Exam, ExamTypeRel, \
    ExamDep, ExamQuestionsScore, ExamCondition, ExamTotalScore
from users.models import Structure, UserProfile
from utils.mixin_utils import LoginRequiredMixin


class ExamQuestionBank(LoginRequiredMixin, View):
    """
    题库
    """

    def get(self, request):
        ret = dict()
        type_list = ExamType.objects.all()
        ret['type_list'] = type_list
        return render(request, 'exam/question_bank.html', ret)

    def post(self, request):
        fields = ['id', 'question', 'type__name']

        filters = dict()
        if request.POST.get('question_type'):
            filters['type_id'] = request.POST.get('question_type')

        muti_choose_list = list(ExamMutiChoose.objects.values(*fields).filter(**filters))
        for m in muti_choose_list:
            m['T_type'] = '多选题'
            muti_choose_answer = ExamMutiChooseAnswer.objects.filter(question_id=m['id']).values('answer')
            answer_list = []
            for a in muti_choose_answer:
                answer_list.append(a['answer'])
            m['answer'] = "、".join(answer_list)
            m['id'] = 'm' + str(m['id'])

        fields.append('answer')
        one_choose_list = list(ExamOneChoose.objects.values(*fields).filter(**filters))
        for o in one_choose_list:
            o['T_type'] = '单选题'
            o['id'] = 'o' + str(o['id'])

        TorF_choose_list = list(ExamTorF.objects.values(*fields).filter(**filters))
        for t in TorF_choose_list:
            t['T_type'] = '判断题'
            t['id'] = 't' + str(t['id'])
            if t['answer'] == '1':
                t['answer'] = '对'
            if t['answer'] == '0':
                t['answer'] = '错'

        all_list = one_choose_list + muti_choose_list + TorF_choose_list
        ret = dict(data=all_list)
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


class ExamQuestionBankImport(LoginRequiredMixin, View):
    """
    题库导入
    """

    def get(self, request):
        ret = dict()
        types = ExamType.objects.all()
        ret['types'] = types
        return render(request, 'exam/question_bank_import.html', ret)

    def post(self, request):
        ret = dict()
        try:
            file = request.FILES.get('que_import')
            type0 = request.POST.get("que_type")
            class0 = request.POST.get("que_class")
            wb = xlrd.open_workbook(filename=None, file_contents=file.read())
            table = wb.sheets()[0]
            nrows = table.nrows  # 行数
            print(type0)
            if type0 == '0':  # 单选题操作
                for i in range(1, nrows):  # 从1开始直接读取数据
                    rowValues = table.row_values(i)  # 一行的数据
                    print(rowValues)  # 这里可以进行其他的操作
                    if rowValues[0] != "" and rowValues[0] != " ":
                        one_choose = ExamOneChoose()
                        one_choose.question = str(rowValues[0])
                        one_choose.A = str(rowValues[1])
                        one_choose.B = str(rowValues[2])
                        one_choose.C = str(rowValues[3])
                        one_choose.D = str(rowValues[4])
                        one_choose.answer = str(rowValues[5])
                        one_choose.type_id = class0
                        one_choose.save()
            elif type0 == '1':  # 多选题操作
                for i in range(1, nrows):  # 从1开始直接读取数据
                    rowValues = table.row_values(i)  # 一行的数据
                    print(rowValues)  # 这里可以进行其他的操作
                    if rowValues[0] != "" and rowValues[0] != " ":
                        muti_choose = ExamMutiChoose()
                        muti_choose.question = str(rowValues[0])
                        muti_choose.A = str(rowValues[1])
                        muti_choose.B = str(rowValues[2])
                        muti_choose.C = str(rowValues[3])
                        muti_choose.D = str(rowValues[4])
                        muti_choose.type_id = class0
                        muti_choose.save()
                        for i in range(len(rowValues[5])):
                            if rowValues[5][i] != " ":
                                muti_choose_answer = ExamMutiChooseAnswer()
                                muti_choose_answer.question = muti_choose
                                muti_choose_answer.answer = rowValues[5][i]
                                muti_choose_answer.save()
            elif type0 == '2':  # 判断题操作
                for i in range(1, nrows):  # 从1开始直接读取数据
                    rowValues = table.row_values(i)  # 一行的数据
                    print(rowValues)  # 这里可以进行其他的操作
                    if rowValues[0] != "" and rowValues[0] != " ":
                        TorF = ExamTorF()
                        TorF.question = rowValues[0]
                        TorF.type_id = class0
                        if rowValues[1] == 1:
                            TorF.answer = '1'
                        elif rowValues[1] == 0:
                            TorF.answer = '0'
                        else:
                            TorF.answer = ' '
                        TorF.save()
            ret["code"] = '0'
            ret["msg"] = "上传成功"
            return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')
        except Exception as e:
            ret["code"] = '-1'
            ret['error'] = str(e)
            return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


class ExamQuestionEdit(LoginRequiredMixin, View):
    """
    题目编辑
    """

    def get(self, request):
        ret = dict()
        id0 = request.GET.get('id')
        id1 = id0[1:]
        data = ''
        if id0.startswith('o'):
            data = ExamOneChoose.objects.filter(id=id1).first()
            ret['type'] = 'o'
        elif id0.startswith('m'):
            data = ExamMutiChoose.objects.filter(id=id1).first()
            ret['type'] = 'm'
            answer_list = ExamMutiChooseAnswer.objects.filter(question=data)
            answer = ""
            for a in answer_list:
                answer += a.answer
            ret['answer'] = answer
        elif id0.startswith('t'):
            data = ExamTorF.objects.filter(id=id1).first()
            ret['type'] = 't'
        ret['data'] = data
        type_list = ExamType.objects.all()
        ret['type_list'] = type_list
        return render(request, 'exam/question_bank_edit.html', ret)

    def post(self, request):
        ret = dict()
        try:
            id0 = request.POST.get('id0')
            type0 = request.POST.get('type0')
            question = request.POST.get('question')
            answer = request.POST.get('answer')
            class0 = request.POST.get('question_class')
            if type0 == 'o':
                if len(answer) != 1 or answer not in "ABCD":
                    raise Exception('答案只能为大写ABCD其中之一，请勿包含空格等其它字符')
                one_choose = ExamOneChoose.objects.filter(id=id0).first()
                one_choose.question = question
                one_choose.A = request.POST.get('A')
                one_choose.B = request.POST.get('B')
                one_choose.C = request.POST.get('C')
                one_choose.D = request.POST.get('D')
                one_choose.answer = answer
                one_choose.type_id = class0
                one_choose.save()
            elif type0 == 'm':
                if len(answer) < 1 or len(answer) > 4:
                    raise Exception('答案只能为大写ABCD，请勿包含空格等其它字符')
                muti_choose = ExamMutiChoose.objects.filter(id=id0).first()
                muti_choose.question = question
                muti_choose.A = request.POST.get('A')
                muti_choose.B = request.POST.get('B')
                muti_choose.C = request.POST.get('C')
                muti_choose.D = request.POST.get('D')
                muti_choose.type_id = class0
                muti_choose.save()
                muti_choose_answer_list = ExamMutiChooseAnswer.objects.filter(question=muti_choose)
                for m in muti_choose_answer_list:
                    m.delete()
                for i in range(len(answer)):
                    if answer[i] not in "ABCD":
                        raise Exception('答案只能为大写ABCD，请勿包含空格等其它字符')
                    muti_choose_answer = ExamMutiChooseAnswer()
                    muti_choose_answer.question = muti_choose
                    muti_choose_answer.answer = answer[i]
                    muti_choose_answer.save()
            elif type0 == 't':
                if len(answer) != 1 or answer not in "01":
                    raise Exception('答案只能为1或0，1为对，0为错，请勿包含空格等其它字符')
                TorF = ExamTorF.objects.filter(id=id0).first()
                TorF.question = question
                TorF.answer = answer
                TorF.type_id = class0
                TorF.save()
            ret['code'] = '0'
        except Exception as e:
            ret['code'] = '-1'
            ret['error'] = str(e)
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


class ExamQuestionDelete(LoginRequiredMixin, View):
    """
    题目删除
    """

    def post(self, request):
        ret = dict()
        try:
            id0 = request.POST.get('id')
            id1 = id0[1:]
            if id0.startswith('o'):
                que = ExamOneChoose.objects.filter(id=id1).first()
                que.delete()
            elif id0.startswith('m'):
                que = ExamMutiChoose.objects.filter(id=id1).first()
                ans = ExamMutiChooseAnswer.objects.filter(question=que)
                for a in ans:
                    a.delete()
                que.delete()
            elif id0.startswith('t'):
                que = ExamTorF.objects.filter(id=id1).first()
                que.delete()
            ret['code'] = '0'
        except Exception as e:
            ret['code'] = '-1'
            ret['error'] = str(e)
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


class ExamTypeManage(LoginRequiredMixin, View):
    """
    试题分类管理
    """

    def get(self, request):
        ret = dict()
        types = ExamType.objects.all()
        ret['types'] = types
        return render(request, 'exam/exam_type.html', ret)

    def post(self, request):
        ret = dict()
        try:
            id0 = request.POST.get('id', None)
            title = request.POST.get('title')
            if id0:
                type0 = ExamType.objects.filter(id=id0).first()
            else:
                type0 = ExamType()
            type0.name = title
            type0.save()
            ret['code'] = '0'
        except Exception as e:
            ret['code'] = '-1'
            ret['error'] = str(e)
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


class ExamList(LoginRequiredMixin, View):
    """
    考试列表
    """

    def get(self, request):
        ret = dict()
        return render(request, 'exam/exam_list.html', ret)

    def post(self, request):
        ret = dict()
        fields = ['id', 'name', 'create_time', 'start_time', 'end_time']
        exam = list(Exam.objects.values(*fields).all())
        now = datetime.date.today()
        for e in exam:
            if now < e['start_time']:
                e['status'] = '未开始'
            elif e['start_time'] <= now <= e['end_time']:
                e['status'] = '进行中'
            elif now > e['end_time']:
                e['status'] = '已结束'
        ret['data'] = exam
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


class ExamCreate(LoginRequiredMixin, View):
    """
    创建考试
    """

    def get(self, request):
        ret = dict()
        types = ExamType.objects.all()
        ret['types'] = types
        departments = Structure.objects.all()
        ret['departments'] = departments
        return render(request, 'exam/exam_create.html', ret)

    def post(self, request):
        ret = dict()
        try:
            user_id = request.session.get('_auth_user_id')
            exam = Exam()
            exam.create_user_id = user_id
            exam.name = request.POST.get("title")
            exam.duration = int(request.POST.get("duration"))

            types = request.POST.getlist("types", [])
            if len(types) == 0:
                raise Exception('考试类型不能为空')

            dep_id_list = []
            if 'to' in request.POST and request.POST['to']:
                dep_id_list = request.POST.getlist('to', [])
            if len(dep_id_list) == 0:
                raise Exception('考试部门不能为空')

            exam.start_time = request.POST.get("start_time")
            exam.end_time = request.POST.get("end_time")

            one_num = request.POST.get('one_num')
            one_score = request.POST.get('one_score')
            if one_num:
                if int(one_num) > 0:
                    if not one_score or float(one_score) <= 0:
                        raise Exception('请正确输入单选题数量与分数')
                    one_data_num = 0  # 判断题目数量是否足够
                    for i in types:
                        one_data = ExamOneChoose.objects.filter(type_id=i)
                        one_data_num += len(one_data)
                    if int(one_num) > one_data_num:
                        raise Exception('单选题数量超出当前题库存储数量')
                    exam.one_num = one_num
                    exam.one_score = float(one_score)
                elif int(one_num) < 0:
                    raise Exception('请正确输入单选题数量与分数')

            muti_num = request.POST.get('muti_num')
            muti_score = request.POST.get('muti_score')
            if muti_num:
                if int(muti_num) > 0:
                    if not muti_score or float(muti_score) <= 0:
                        raise Exception('请正确输入多选题数量与分数')
                    muti_data_num = 0  # 判断题目数量是否足够
                    for i in types:
                        muti_data = ExamMutiChoose.objects.filter(type_id=i)
                        muti_data_num += len(muti_data)
                    if int(muti_num) > muti_data_num:
                        raise Exception('多选题数量超出当前题库存储数量')
                    exam.muti_num = muti_num
                    exam.muti_score = float(muti_score)
                elif int(muti_num) < 0:
                    raise Exception('请正确输入多选题数量与分数')

            TorF_num = request.POST.get('TorF_num')
            TorF_score = request.POST.get('TorF_score')
            if TorF_num:
                if int(TorF_num) > 0:
                    if not TorF_score or float(TorF_score) <= 0:
                        raise Exception('请正确输入判断题数量与分数')
                    TorF_data_num = 0  # 判断题目数量是否足够
                    for i in types:
                        TorF_data = ExamTorF.objects.filter(type_id=i)
                        TorF_data_num += len(TorF_data)
                    if int(TorF_num) > TorF_data_num:
                        raise Exception('判断题数量超出当前题库存储数量')
                    exam.TorF_num = TorF_num
                    exam.TorF_score = float(TorF_score)
                elif int(TorF_num) < 0:
                    raise Exception('请正确输入判断题数量与分数')

            exam.total_score = float(request.POST.get('total_score'))
            if exam.total_score <= 0:
                raise Exception('总分不能小于等于0')
            exam.pass_score = float(request.POST.get('pass_score'))
            if exam.total_score < exam.pass_score:
                raise Exception('总分不能小于及格分数')

            exam.save()
            for t in types:
                exam_type = ExamTypeRel()
                exam_type.exam = exam
                exam_type.type_id = t
                exam_type.save()
            for d in dep_id_list:
                exam_dep = ExamDep()
                exam_dep.exam = exam
                exam_dep.dep_id = d
                exam_dep.save()
            ret['code'] = '0'
        except Exception as e:
            ret['code'] = '-1'
            ret['error'] = str(e)
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


class ExamDetail(LoginRequiredMixin, View):
    """
    考试详情
    """

    def get(self, request):
        ret = dict()
        id0 = request.GET.get("id")
        exam = Exam.objects.filter(id=id0).first()
        ret['exam'] = exam

        exam_type_list = ExamTypeRel.objects.filter(exam=exam)
        exam_type = []
        for i in exam_type_list:
            exam_type.append(i.type.name)
        exam_type = '、'.join(exam_type)
        ret['exam_type'] = exam_type

        dep_list = ExamDep.objects.filter(exam=exam)
        exam_dep = []
        for i in dep_list:
            exam_dep.append(i.dep.title)
        exam_dep = '、'.join(exam_dep)
        ret['exam_dep'] = exam_dep
        return render(request, 'exam/exam_detail.html', ret)


# 我的工作台
class ExamShowList(LoginRequiredMixin, View):
    """
    考试列表
    """

    def get(self, request):
        ret = dict()
        user_id = request.session.get("_auth_user_id")
        user = UserProfile.objects.filter(id=user_id).first()
        now = datetime.date.today()
        exam_list = list(ExamDep.objects.filter(dep_id=user.department_id, exam__start_time__lte=now,
                                                exam__end_time__gte=now))
        now_time = datetime.datetime.now()
        for exam in exam_list:
            condition = ExamCondition.objects.filter(user_id=user_id, exam_id=exam.exam.id).first()
            if condition:
                if condition.is_submit:
                    exam.status = '已完成'
                else:
                    delta = datetime.timedelta(minutes=int(exam.exam.duration))
                    if now_time > condition.start_time + delta:
                        exam.status = '已超时'

            total = ExamTotalScore.objects.filter(user_id=user_id, exam_id=exam.exam.id).first()
            if total:
                exam.total_score = total.score
                exam.pass0 = total.is_pass
        ret['exam_list'] = exam_list
        return render(request, "exam/exam_show_list.html", ret)

    def post(self, request):
        """
        生成试卷
        :param request:
        :return:
        """
        ret = dict()
        try:
            exam_id = request.POST.get('id0')
            ret["exam_id"] = exam_id
            user_id = request.session.get('_auth_user_id')
            started_exam = ExamQuestionsScore.objects.filter(exam_id=exam_id, user_id=user_id)
            if len(started_exam) != 0:
                pass
            else:
                exam = Exam.objects.filter(id=exam_id).first()
                exam_types = ExamTypeRel.objects.filter(exam=exam)

                # 单选题
                if exam.one_num:
                    one_num = int(exam.one_num)
                    if one_num > 0:
                        one_choose_bank = []
                        for t in exam_types:
                            one_choose_list = list(ExamOneChoose.objects.filter(type_id=t.type_id))
                            one_choose_bank += one_choose_list
                        one_choose_ques = random.sample(one_choose_bank, one_num)
                        for i in range(one_num):
                            que = ExamQuestionsScore()
                            que.user_id = user_id
                            que.exam = exam
                            que.one_choose = one_choose_ques[i]
                            que.num = i + 1
                            que.save()

                # 多选题
                if exam.muti_num:
                    muti_num = int(exam.muti_num)
                    if muti_num > 0:
                        muti_choose_bank = []
                        for t in exam_types:
                            muti_choose_list = list(ExamMutiChoose.objects.filter(type_id=t.type_id))
                            muti_choose_bank += muti_choose_list
                        muti_choose_ques = random.sample(muti_choose_bank, muti_num)
                        for i in range(muti_num):
                            que = ExamQuestionsScore()
                            que.user_id = user_id
                            que.exam = exam
                            que.muti_choose = muti_choose_ques[i]
                            que.num = i + 1
                            que.save()

                # 判断题
                if exam.TorF_num:
                    TorF_num = int(exam.TorF_num)
                    if TorF_num > 0:
                        TorF_choose_bank = []
                        for t in exam_types:
                            TorF_choose_list = list(ExamTorF.objects.filter(type_id=t.type_id))
                            TorF_choose_bank += TorF_choose_list
                        TorF_choose_ques = random.sample(TorF_choose_bank, TorF_num)
                        for i in range(TorF_num):
                            que = ExamQuestionsScore()
                            que.user_id = user_id
                            que.exam = exam
                            que.TorF_choose = TorF_choose_ques[i]
                            que.num = i + 1
                            que.save()

            condition = ExamCondition()
            condition.exam_id = exam_id
            condition.user_id = user_id
            condition.save()
            ret['code'] = '0'
        except Exception as e:
            ret['code'] = '-1'
            ret['error'] = str(e)
        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


class ExamStart(LoginRequiredMixin, View):
    """
    考试页面
    """

    def get(self, request):
        ret = dict()
        exam_id = request.GET.get('id0')
        exam = Exam.objects.filter(id=exam_id).first()
        ret['exam'] = exam
        user_id = request.session.get('_auth_user_id')

        condition = ExamCondition.objects.filter(user_id=user_id, exam_id=exam.id).first()
        k = 0
        if condition:
            now_time = datetime.datetime.now()
            delta = datetime.timedelta(minutes=int(exam.duration))
            if condition.start_time < now_time < condition.start_time + delta:
                pass
            else:
                k = -1
            if condition.is_submit:
                k = -1
        if k == -1:
            return render(request, 'page404.html')

        # 剩余时间计算
        now = datetime.datetime.now()
        delta = datetime.timedelta(minutes=int(exam.duration))
        duration = condition.start_time + delta - now
        duration = str(duration).split('.')[0]
        ret['duration'] = duration

        one_choose_list = ExamQuestionsScore.objects.filter(Q(exam_id=exam_id), Q(user_id=user_id),
                                                            ~Q(one_choose_id=None))
        if len(one_choose_list) != 0:
            ret['one_choose_list'] = one_choose_list
            ret['one_choose_total_score'] = int(exam.one_num) * float(exam.one_score)

        muti_choose_list = ExamQuestionsScore.objects.filter(Q(exam_id=exam_id), Q(user_id=user_id),
                                                             ~Q(muti_choose_id=None))
        if len(muti_choose_list) != 0:
            ret['muti_choose_list'] = muti_choose_list
            ret['muti_choose_total_score'] = int(exam.muti_num) * float(exam.muti_score)

        TorF_choose_list = ExamQuestionsScore.objects.filter(Q(exam_id=exam_id), Q(user_id=user_id),
                                                             ~Q(TorF_choose_id=None))
        if len(TorF_choose_list) != 0:
            ret['TorF_choose_list'] = TorF_choose_list
            ret['TorF_choose_total_score'] = int(exam.TorF_num) * float(exam.TorF_score)
        ret['total_num'] = len(one_choose_list) + len(muti_choose_list) + len(TorF_choose_list)
        return render(request, 'exam/exam_start.html', ret)

    def post(self, request):
        """
        试题选项保存
        :param request:
        :return:
        """
        status = request.POST.get('status')
        if status == '1':
            print(status)  # 状态保持
        elif status is None:
            user_id = request.session.get('_auth_user_id')
            exam_id = request.POST.get('exam_id')
            type0 = request.POST.get('type')
            num = request.POST.get('num')
            option = request.POST.get('option')

            if type0 == "0":  # 单选题
                que = ExamQuestionsScore.objects.filter(Q(user_id=user_id), Q(exam_id=exam_id), ~Q(one_choose=None),
                                                        Q(num=num)).first()
                if option == '1':
                    que.user_answer = 'A'
                elif option == '2':
                    que.user_answer = 'B'
                elif option == '3':
                    que.user_answer = 'C'
                elif option == '4':
                    que.user_answer = 'D'
                que.save()
            elif type0 == '2':  # 判断题
                que = ExamQuestionsScore.objects.filter(Q(user_id=user_id), Q(exam_id=exam_id), ~Q(TorF_choose=None),
                                                        Q(num=num)).first()
                if option == '1':
                    que.user_answer = '1'
                elif option == '0':
                    que.user_answer = '0'
                que.save()
            elif type0 == '1':  # 多选题
                print(1)
                que = ExamQuestionsScore.objects.filter(Q(user_id=user_id), Q(exam_id=exam_id), ~Q(muti_choose=None),
                                                        Q(num=num)).first()
                if option == '1':
                    if que.user_answer:
                        if 'A' in que.user_answer:
                            que.user_answer = que.user_answer.replace('A', '')
                        else:
                            que.user_answer += 'A'
                    else:
                        que.user_answer = 'A'
                elif option == '2':
                    if que.user_answer:
                        if 'B' in que.user_answer:
                            que.user_answer = que.user_answer.replace('B', '')
                        else:
                            que.user_answer += 'B'
                    else:
                        que.user_answer = 'B'
                elif option == '3':
                    if que.user_answer:
                        if 'C' in que.user_answer:
                            que.user_answer = que.user_answer.replace('C', '')
                        else:
                            que.user_answer += 'C'
                    else:
                        que.user_answer = 'C'
                elif option == '4':
                    if que.user_answer:
                        if 'D' in que.user_answer:
                            que.user_answer = que.user_answer.replace('D', '')
                        else:
                            que.user_answer += 'D'
                    else:
                        que.user_answer = 'D'
                a = list(que.user_answer)
                a.sort()
                a = "".join(a)
                que.user_answer = a
                que.save()
        return HttpResponse()


class ExamAjax(LoginRequiredMixin, View):
    def get(self, request):
        """
        交卷及分数计算
        :param request:
        :return:
        """
        ret = dict()
        user_id = request.session.get('_auth_user_id')
        exam_id = request.GET.get("id0")
        exam = Exam.objects.filter(id=exam_id).first()
        ques = ExamQuestionsScore.objects.filter(exam_id=exam_id, user_id=user_id)
        total_score = 0

        for que in ques:
            # 单选题：
            if que.one_choose is not None:
                if que.user_answer:
                    if que.user_answer == que.one_choose.answer:
                        que.score = exam.one_score
                        que.is_right = True
                    else:
                        que.score = 0
                else:
                    que.score = 0

            # 判断题
            elif que.TorF_choose is not None:
                if que.user_answer:
                    if que.user_answer == que.TorF_choose.answer:
                        que.score = exam.TorF_score
                        que.is_right = True
                    else:
                        que.score = 0
                else:
                    que.score = 0

            # 多选题
            elif que.muti_choose is not None:
                if que.user_answer:
                    muti_answers = ExamMutiChooseAnswer.objects.filter(question=que.muti_choose)
                    answer_list = list(que.user_answer)
                    for m in muti_answers:
                        if m.answer in answer_list:
                            answer_list.remove(m.answer)
                        else:
                            que.score = 0
                            break
                    else:
                        if len(answer_list) == 0:
                            que.score = exam.muti_score
                            que.is_right = True
                        else:
                            que.score = 0
                else:
                    que.score = 0
            total_score += que.score
            que.save()

        # 总成绩
        total = ExamTotalScore()
        total.exam_id = exam_id
        total.user_id = user_id
        total.score = total_score
        if total.score >= exam.pass_score:
            total.is_pass = True
        else:
            total.is_pass = False
        total.save()

        # 考试情况
        condition = ExamCondition.objects.filter(exam_id=exam_id, user_id=user_id).first()
        condition.is_submit = True
        now = datetime.datetime.now()
        duration = (now - condition.start_time).total_seconds()
        condition.time = duration // 60
        condition.save()

        return HttpResponse(json.dumps(ret, cls=DjangoJSONEncoder), content_type='application/json')


class ExamScoreDetail(LoginRequiredMixin, View):
    """
    分数详情页面
    """
    def get(self, request):
        ret = dict()
        user_id = request.session.get('_auth_user_id')
        exam_id = request.GET.get('id0')
        exam = Exam.objects.filter(id=exam_id).first()
        ret['exam'] = exam

        one_choose_list = ExamQuestionsScore.objects.filter(Q(exam_id=exam_id), Q(user_id=user_id),
                                                            ~Q(one_choose_id=None))
        if len(one_choose_list) != 0:
            ret['one_choose_list'] = one_choose_list
            ret['one_choose_total_score'] = int(exam.one_num) * float(exam.one_score)

        muti_choose_list = ExamQuestionsScore.objects.filter(Q(exam_id=exam_id), Q(user_id=user_id),
                                                             ~Q(muti_choose_id=None))
        if len(muti_choose_list) != 0:
            for m in muti_choose_list:
                m_answer_list = ExamMutiChooseAnswer.objects.filter(question=m.muti_choose)
                m_answer = []
                for n in m_answer_list:
                    m_answer.append(n.answer)
                m_answer.sort()
                m.m_answer = ''.join(m_answer)
            ret['muti_choose_list'] = muti_choose_list
            ret['muti_choose_total_score'] = int(exam.muti_num) * float(exam.muti_score)

        TorF_choose_list = ExamQuestionsScore.objects.filter(Q(exam_id=exam_id), Q(user_id=user_id),
                                                             ~Q(TorF_choose_id=None))
        if len(TorF_choose_list) != 0:
            ret['TorF_choose_list'] = TorF_choose_list
            ret['TorF_choose_total_score'] = int(exam.TorF_num) * float(exam.TorF_score)

        total = ExamTotalScore.objects.filter(exam_id=exam_id, user_id=user_id).first()
        ret['total'] = total
        return render(request, 'exam/score_detail.html', ret)


class ExamScoreReport(LoginRequiredMixin, View):
    """
    成绩单
    """
    def get(self, request):
        ret = dict()
        exam_id = request.GET.get("id")
        ret['exam_id'] = exam_id
        deps = ExamDep.objects.filter(exam_id=exam_id)
        user_list = []
        for dep in deps:
            users = list(UserProfile.objects.filter(department=dep.dep, is_active='1'))
            user_list += users

        score_list = []
        for user in user_list:
            total = ExamTotalScore.objects.filter(exam_id=exam_id, user_id=user.id).first()
            if total:
                score_list.append(total)
            else:
                score_list.append(user)
        ret['score_list'] = score_list

        return render(request, 'exam/score_report.html', ret)


class ExamHistory(LoginRequiredMixin, View):
    """
    往期考试
    """
    def get(self, request):
        ret = dict()
        user_id = request.session.get("_auth_user_id")
        user = UserProfile.objects.filter(id=user_id).first()
        now = datetime.date.today()
        exam_list = list(ExamDep.objects.filter(dep_id=user.department_id, exam__end_time__lt=now))
        for exam in exam_list:
            condition = ExamCondition.objects.filter(user_id=user_id, exam_id=exam.exam.id).first()
            if condition:
                if condition.is_submit:
                    exam.status = '1'

            total = ExamTotalScore.objects.filter(user_id=user_id, exam_id=exam.exam.id).first()
            if total:
                exam.total_score = total.score
                exam.pass0 = total.is_pass
        ret['exam_list'] = exam_list
        return render(request, 'exam/exam_history_list.html', ret)