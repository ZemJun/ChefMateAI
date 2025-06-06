# ChefMateAI\recipes\views.py
from django.shortcuts import render

def test_page(request):
    """渲染测试页面"""
    return render(request, 'recipes/test_page.html')
