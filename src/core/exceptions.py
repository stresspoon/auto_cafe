"""사용자 정의 예외 클래스 모듈."""


class QOK6Exception(Exception):
    """QOK6 시스템의 기본 예외 클래스."""
    pass


class ConfigurationError(QOK6Exception):
    """설정 관련 오류 발생 시 사용되는 예외."""
    pass


class NaverCrawlerError(QOK6Exception):
    """네이버 크롤링 관련 오류 발생 시 사용되는 예외."""
    pass


class LoginFailedError(NaverCrawlerError):
    """네이버 로그인 실패 시 사용되는 예외."""
    pass


class CrawlingError(NaverCrawlerError):
    """게시글 크롤링 실패 시 사용되는 예외."""
    pass


class GoogleSheetsError(QOK6Exception):
    """구글 시트 연동 관련 오류 발생 시 사용되는 예외."""
    pass


class AuthenticationError(GoogleSheetsError):
    """구글 API 인증 실패 시 사용되는 예외."""
    pass


class SheetUpdateError(GoogleSheetsError):
    """시트 업데이트 실패 시 사용되는 예외."""
    pass


class ParsingError(QOK6Exception):
    """데이터 파싱 관련 오류 발생 시 사용되는 예외."""
    pass


class SchedulingError(QOK6Exception):
    """스케줄링 관련 오류 발생 시 사용되는 예외."""
    pass