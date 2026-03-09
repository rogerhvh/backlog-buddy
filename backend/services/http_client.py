import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def create_retry_session(
    total_retries: int = 3,
    backoff_factor: float = 0.5,
    pool_connections: int = 20,
    pool_maxsize: int = 20,
) -> requests.Session:
    retry = Retry(
        total=total_retries,
        read=total_retries,
        connect=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
    )

    adapter = HTTPAdapter(
        max_retries=retry,
        pool_connections=pool_connections,
        pool_maxsize=pool_maxsize,
    )

    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session