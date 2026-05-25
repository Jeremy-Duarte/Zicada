from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML


class BaseReport(ABC):
    def __init__(self, request, **params):
        self.request = request
        self.user = request.user
        self.params = self._normalize_params(params)

    def _normalize_params(self, params):
        date_from = params.get('date_from', '')
        date_to = params.get('date_to', '')
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not date_to:
            date_to = datetime.now().strftime('%Y-%m-%d')
        return {
            'date_from': datetime.strptime(date_from, '%Y-%m-%d').date(),
            'date_to': datetime.strptime(date_to, '%Y-%m-%d').date(),
            'include_charts': params.get('include_charts', False),
            'include_tables': params.get('include_tables', True),
        }

    @abstractmethod
    def get_data(self):
        pass

    @abstractmethod
    def get_template(self):
        pass

    def get_filename(self):
        from_date = self.params['date_from'].strftime('%Y%m%d')
        to_date = self.params['date_to'].strftime('%Y%m%d')
        return f"{self.__class__.__name__.lower()}_{from_date}_{to_date}.pdf"

    def render_pdf(self):
        context = {
            'report_title': self.get_title(),
            'generated_at': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            'user': self.user,
            'params': self.params,
            'data': self.get_data(),
        }
        html_string = render_to_string(self.get_template(), context)
        pdf = HTML(string=html_string).write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{self.get_filename()}"'
        return response

    def preview(self):
        return {
            'report_title': self.get_title(),
            'params': self.params,
            'data': self.get_data(),
        }

    @abstractmethod
    def get_title(self):
        pass