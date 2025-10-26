from django.shortcuts import render

def gt_map(request):
    return render(request, 'mapview/map.html')