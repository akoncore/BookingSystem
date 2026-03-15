#Python imports
import pytz

from django.conf import settings
from django.utils import translation, timezone


from rest_framework_simplejwt.authentication import JWTAuthentication


class LanguageAndTimezoneMiddleware:

    """
    Request келген сайын:
      1. JWT токенінен пайдаланушыны аутентификациялайды (бар болса)
      2. Тілді анықтап, translation.activate(lang) шақырады
      3. Timezone белсендіреді
    """

    def __init__(self,get_response):
        self.get_response = get_response
        self._jwt_auth = JWTAuthentication()

    def __call__(self, request,*args, **kwds):
        #Через JWT колданушы аныктау
        self._try_authenticate_jwt(request)

        #Тилди аныктап белсендиру
        lang = self._resolve_languages(request)
        translation.activate(lang)
        request.LANGUAGE_CODE = lang

        #Timezone
        self._activate_timezone(request)

        try:
            response = self.get_response(request)
        finally:
            translation.deactivate()
            timezone.deactivate()
            
        return response
        
    #JWT Authentication
    def _try_authenticate_jwt(self,request):
        """
        Authorization header-дан JWT токенін оқып,
        request.user-ге пайдаланушыны орнатады.
        Токен жоқ немесе жарамсыз болса — тыныш өтеді.
        """

        if request.user.is_authenticated:
            return

        try:
            result = self._jwt_auth.authenticate(request)
            if result is not None:
                request.user, _ = result
        except Exception:
            pass

    #Language
    def _resolve_languages(self,request):
        """
        Тілді кезекпен тексереді, бірінші табылған тілді қайтарады.
        """
        supported: set = set(getattr(settings, 'SUPPORTED_LANGUAGES',['en','ru','kk']))

        return(
            self._lang_from_user(request,supported)
            or self._lang_from_query(request,supported)
            or self._lang_from_accept_header(request,supported)
            or getattr(settings,'LANGUAGE_CODE','en')
        )    
    
    @staticmethod
    def _lang_from_user(request,supported:set)->str | None:
        
        if request.user.is_authenticated:
            lang =getattr(request.user, 'preferred_language',None)
            if lang in supported:
                return lang
        return None
    
    @staticmethod
    def _lang_from_query(request,supported:set)->str | None:

        lang = request.GET.get('lang')
        return lang if lang in supported else None

    @staticmethod
    def _lang_from_accept_header(request,supported:set)-> str | None:

        accept_header = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        for segment in accept_header.split(','):
            code = segment.strip().split(';')[0].strip()[:2].lower()
            if code in supported:
                return code
        return None
    

    #Timezone
    def _activate_timezone(self,request):

        tz = self._resolve_timezone(request)
        timezone.activate(tz)

    @staticmethod
    def _resolve_timezone(request):
        if request.user.is_authenticated:
            tz_name = getattr(request.user, 'timezone', None)
            if tz_name:
                try:
                    return pytz.timezone(tz_name)
                except pytz.exceptions.UnknownTimeZoneError:
                    pass
        return pytz.utc
        
