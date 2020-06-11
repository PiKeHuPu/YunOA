from django.db import models
# Create your models here.
from users.models import Structure, UserProfile


class Exam(models.Model):
    """
    考试
    """
    name = models.CharField(max_length=50, verbose_name="考试名称")
    start_time = models.DateField(verbose_name="开始时间")
    end_time = models.DateField(verbose_name="结束时间")
    one_num = models.CharField(max_length=5, blank=True, null=True, verbose_name="单选题数量")
    one_score = models.FloatField(blank=True, null=True, verbose_name="单选题分数")
    muti_num = models.CharField(max_length=5, blank=True, null=True, verbose_name="多选题数量")
    muti_score = models.FloatField(blank=True, null=True, verbose_name="多选题分数")
    TorF_num = models.CharField(max_length=5, blank=True, null=True, verbose_name="判断题数量")
    TorF_score = models.FloatField(blank=True, null=True, verbose_name="判断题分数")
    total_score = models.FloatField(verbose_name="考试总分")
    pass_score = models.FloatField(verbose_name="及格分数")
    create_user = models.ForeignKey(UserProfile, verbose_name='创建人')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    duration = models.IntegerField(verbose_name='考试时长')


class ExamType(models.Model):
    """
    考试类型
    """
    name = models.CharField(max_length=50, verbose_name="考试类型名称")


class ExamDep(models.Model):
    """
    考试部门
    """
    exam = models.ForeignKey(Exam, verbose_name="考试关联")
    dep = models.ForeignKey(Structure, verbose_name="部门关联")


class ExamTypeRel(models.Model):
    """
    考试类型关联
    """
    exam = models.ForeignKey(Exam, verbose_name="考试关联")
    type = models.ForeignKey(ExamType, verbose_name="类型关联")


class ExamOneChoose(models.Model):
    """
    单选题
    """
    question = models.CharField(max_length=200, verbose_name="题干")
    A = models.CharField(max_length=200, verbose_name="选项A")
    B = models.CharField(max_length=200, verbose_name="选项B")
    C = models.CharField(max_length=200, verbose_name="选项C")
    D = models.CharField(max_length=200, verbose_name="选项D")
    answer = models.CharField(max_length=1, verbose_name="答案")
    type = models.ForeignKey(ExamType, verbose_name="题目类型")


class ExamMutiChoose(models.Model):
    """
    多选题题干
    """
    question = models.CharField(max_length=200, verbose_name="题干")
    A = models.CharField(max_length=200, verbose_name="选项A")
    B = models.CharField(max_length=200, verbose_name="选项B")
    C = models.CharField(max_length=200, verbose_name="选项C")
    D = models.CharField(max_length=200, verbose_name="选项D")
    type = models.ForeignKey(ExamType, verbose_name="题目类型")


class ExamMutiChooseAnswer(models.Model):
    """
    多选题答案关联
    """
    question = models.ForeignKey(ExamMutiChoose, verbose_name="多选题关联")
    answer = models.CharField(max_length=1, verbose_name="答案关联")


class ExamTorF(models.Model):
    """
    判断题
    """
    question = models.CharField(max_length=200, verbose_name="题干")
    answer = models.CharField(max_length=1, verbose_name="答案")
    type = models.ForeignKey(ExamType, verbose_name="题目类型")


class ExamQuestionsScore(models.Model):
    """
    考试人员试题得分情况
    """
    user = models.ForeignKey(UserProfile, verbose_name="用户")
    exam = models.ForeignKey(Exam, verbose_name="考试关联")
    one_choose = models.ForeignKey(ExamOneChoose, blank=True, null=True, verbose_name="单选题关联")
    muti_choose = models.ForeignKey(ExamMutiChoose, blank=True, null=True, verbose_name="多选题关联")
    TorF_choose = models.ForeignKey(ExamTorF, blank=True, null=True, verbose_name="判断题关联")
    user_answer = models.CharField(max_length=10, blank=True, null=True, verbose_name="用户答案")
    num = models.CharField(max_length=5, verbose_name="题目序号")
    is_right = models.BooleanField(default=False, verbose_name="是否正确")
    score = models.FloatField(blank=True, null=True, verbose_name="分值")


class ExamTotalScore(models.Model):
    """
    考试总成绩
    """
    user = models.ForeignKey(UserProfile, verbose_name="用户")
    exam = models.ForeignKey(Exam, verbose_name="考试关联")
    score = models.IntegerField(verbose_name="总成绩")
    is_pass = models.BooleanField(verbose_name="是否及格")


class ExamCondition(models.Model):
    """
    考试答题情况
    """
    user = models.ForeignKey(UserProfile, verbose_name="用户")
    exam = models.ForeignKey(Exam, verbose_name="考试关联")
    start_time = models.DateTimeField(auto_now_add=True, verbose_name="开始时间")
    time = models.IntegerField(default=0, verbose_name="答题时间记录")
    is_submit = models.BooleanField(default=False, verbose_name="是否交卷")


