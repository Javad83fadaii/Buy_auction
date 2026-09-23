from dataclasses import dataclass


@dataclass(frozen=True)
class RoleDefinition:
    name: str
    title: str


ADMIN_ROLE = 'ADMIN'
MANAGER_ROLE = 'MANAGER'
OPERATOR_ROLE = 'OPERATOR'
EXPERT_ROLE = 'EXPERT'

ROLE_DEFINITIONS = (
    RoleDefinition(name=ADMIN_ROLE, title='ادمین'),
    RoleDefinition(name=MANAGER_ROLE, title='مدیر'),
    RoleDefinition(name=OPERATOR_ROLE, title='اپراتور'),
    RoleDefinition(name=EXPERT_ROLE, title='کارشناس'),
)

ROLE_NAME_SET = {role.name for role in ROLE_DEFINITIONS}
ROLE_TITLE_MAP = {role.name: role.title for role in ROLE_DEFINITIONS}


def get_role_title(role_name: str) -> str:
    return ROLE_TITLE_MAP.get(role_name, role_name or '-')
