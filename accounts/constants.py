from dataclasses import dataclass


@dataclass(frozen=True)
class RoleDefinition:
    name: str
    title: str


ADMIN_ROLE = 'ADMIN'
OPERATOR_ROLE = 'OPERATOR'
VIEWER_ROLE = 'VIEWER'

ROLE_DEFINITIONS = (
    RoleDefinition(name=ADMIN_ROLE, title='مدیر سیستم'),
    RoleDefinition(name=OPERATOR_ROLE, title='اپراتور'),
    RoleDefinition(name=VIEWER_ROLE, title='مشاهده‌کننده'),
)

ROLE_NAME_SET = {role.name for role in ROLE_DEFINITIONS}
ROLE_TITLE_MAP = {role.name: role.title for role in ROLE_DEFINITIONS}


def get_role_title(role_name: str) -> str:
    return ROLE_TITLE_MAP.get(role_name, role_name or '-')
