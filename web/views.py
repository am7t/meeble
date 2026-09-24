from django.http import JsonResponse
from django.shortcuts import render


def home(request):
    return render(request, "web/index.html")


def health(request):
    return JsonResponse({"status": "ok", "service": "meeble-local"})
