from datetime import datetime
from http.client import HTTPResponse
from django.template.loader import get_template
from django.views import View
from xhtml2pdf import pisa
from django.http import HttpResponse
import requests
from django.db.models import Q

def render_to_pdf(template_path, context_dict={}, name="report"):
    template = get_template(template_path)
    ctx = context_dict
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename=Rapport_' + str(name) + str(datetime.now()) + '.pdf'

    html = template.render(context_dict)

    pisa_status = pisa.CreatePDF(
        html, dest=response
    )

    if pisa_status.err:
        return HttpResponse('Nous avons quelques erreurs<pre>'+ html +'</pre>')
    
    return response