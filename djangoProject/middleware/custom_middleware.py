from django.utils.deprecation import MiddlewareMixin

class SecurePartitionedCookieMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        for cookie_name in ['csrftoken', 'sessionid']:
            if cookie_name in response.cookies:
                cookie = response.cookies[cookie_name]
                cookie['samesite'] = 'None'
                cookie['secure'] = True
                cookie['httponly'] = True
                
                # Manually append the Partitioned attribute to the Set-Cookie header
                if 'Set-Cookie' in response.headers:
                    response.headers['Set-Cookie'] = response.headers['Set-Cookie'].replace(
                        f"{cookie_name}=",
                        f"{cookie_name}; Partitioned;"
                    )

        return response
