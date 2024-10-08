from datetime import timedelta

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from  django.db.models import Sum

from AnalysisApp.AnalysisApp.models import passbook
from AnalysisApp.AnalysisApp.serializers import ResponseSerializer

CATEGORY_MAPPING = {
    # todo 추가
    0 : '통신',
    1 : '저축'
}

def get_summary_data(transactions) :
    deposit_total = transactions.filter(input_type=0).aggregate(total = Sum('tran_amt'))['total'] or 0 # 입금 합계
    withdraw_total  = transactions.filter(input_type=1).aggregate(total=Sum('tran_amt'))['total'] or 0 # 출금 합계

    #카테고리별 합계 계산
    category_sums = transactions.filter(input_type=1).values('category').annotate(total=Sum('tran_amt')) # 카테고리별 합계
    category_sums = sorted(category_sums, key=lambda x: x['total'], reverse=True)[:3] # 탑3

    # 탑 카테고리 3개
    top_categories = [
        {
            'category' : CATEGORY_MAPPING.get(item['category'], '알 수 없음'),
            'amount' : item['total']
        }
        for item in category_sums
    ]

    return {
        "deposit_total" : deposit_total,
        "withdraw_total" : withdraw_total,
        "top_categories" : top_categories
    }

@api_view(['GET'])
def transaction_summary(request):
    today = timezone.now()
    one_week_ago = today - timedelta(days=7)
    one_month_ago = today - timedelta(days=30)

    # 일간 데이터
    daily_transactions = passbook.objects.filter(tran_date_time__date = today.date())
    daily_summary_data = get_summary_data(daily_transactions)

    # 주간 데이터
    weekly_transactions = passbook.objects.filter(tran_date_time__gte = one_week_ago)
    weekly_summary_data = get_summary_data(weekly_transactions)

    # 월간 데이터
    monthly_transactions = passbook.objects.filter(tran_date_time__gte = one_month_ago)
    monthly_summary_data = get_summary_data(monthly_transactions)

    response_data = {
        'monthly_summary_data' : monthly_summary_data,
        'weekly_summary_data' : weekly_summary_data,
        'daily_summary_data' : daily_summary_data,
    }

    serializer = ResponseSerializer(response_data)
    return Response(serializer.data)