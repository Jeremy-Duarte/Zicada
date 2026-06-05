from django.urls import reverse, NoReverseMatch
from functools import lru_cache

@lru_cache(maxsize=128)
def lazy_reverse(view_name, **kwargs):
    """
    Reverse seguro que resuelve la URL solo cuando se accede a ella.
    Útil para usar en formularios en tiempo de importación.
    """
    class LazyURL:
        def __init__(self, view_name, kwargs):
            self.view_name = view_name
            self.kwargs = kwargs
            self._url = None
        
        def __str__(self):
            if self._url is None:
                try:
                    self._url = reverse(self.view_name, kwargs=self.kwargs)
                except NoReverseMatch:
                    # Si falla, construir URL manualmente como fallback
                    if 'slug' in self.kwargs:
                        if 'collection_detail' in self.view_name:
                            self._url = f'/productos/colecciones/{self.kwargs["slug"]}/'
                        elif 'product_detail' in self.view_name:
                            self._url = f'/productos/{self.kwargs["slug"]}/'
                    else:
                        self._url = f'/error/{self.view_name}/'
            return self._url
        
        def __eq__(self, other):
            return str(self) == str(other)
        
        def __hash__(self):
            return hash(str(self))
    
    return LazyURL(view_name, kwargs)


def safe_reverse(view_name, **kwargs):
    """
    Versión simple que devuelve None si falla.
    """
    try:
        return reverse(view_name, **kwargs)
    except NoReverseMatch:
        return None