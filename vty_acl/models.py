from dataclasses import dataclass


@dataclass
class AclEntry:
    ip: str
    wildcard: str
