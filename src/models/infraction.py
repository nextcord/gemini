from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from asyncpg import Pool
from nextcord import Member, Embed


class InfractionType:
    NOTE = 0
    WARN = 1
    MUTE = 2
    KICK = 3
    BAN = 4


TYPES = {
    0: "Note",
    1: "Warn",
    2: "Mute",
    3: "Kick",
    4: "Ban",
}


@dataclass
class Infraction:
    pool: Pool
    id: int
    member_id: int
    member_name: str
    staff_id: int
    staff_name: str
    infr_type: int
    reason: str
    created: datetime
    expires: Optional[datetime] = None
    expired: Optional[bool] = False

    @classmethod
    async def new(
        cls,
        pool: Pool,
        member: Member,
        staff: Member,
        type: int,
        reason: str,
        expires: datetime = None,
    ) -> "Infraction":
        record = await pool.fetchrow(
            "INSERT INTO Infractions (member_id, member_name, staff_id, staff_name, infr_type, reason, created, expires)"
            "VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING *;",
            member.id,
            str(member),
            staff.id,
            str(staff),
            type,
            reason,
            datetime.utcnow(),
            expires,
        )

        return cls(pool, **record)

    @classmethod
    async def find_member_infractions(
        cls,
        pool: Pool,
        member: Member,
    ) -> List["Infraction"]:
        infractions = await pool.fetch(
            "SELECT * FROM Infractions WHERE member_id = $1;", member.id
        )

        return [cls(pool, **infraction) for infraction in infractions]

    @classmethod
    async def find_expired_infractions(
        cls,
        pool: Pool,
    ) -> List["Infraction"]:
        infractions = await pool.fetch(
            "SELECT * FROM Infractions WHERE expired = FALSE AND expires < $1;",
            datetime.utcnow(),
        )

        return [cls(pool, **infraction) for infraction in infractions]

    @classmethod
    async def find_infraction(
        cls,
        pool: Pool,
        id: int,
    ) -> Optional["Infraction"]:
        infraction = await pool.fetchrow("SELECT * FROM Infractions WHERE id = $1;", id)

        return cls(pool, **infraction)

    def embed(self) -> Embed:
        colour = {
            0: 0x34cfeb,
            1: 0xc0eb34,
            2: 0xebb434,
            3: 0xeb8334,
            4: 0xff0000,
        }.get(self.infr_type, 0x34cfeb)

        embed = Embed(
            colour=colour,
            timestamp=self.created,
            title=f"Infraction: {self.id} | {self.member_name}",
            description=(
                f"User: {self.member_name} ({self.member_id} | <@{self.member_id}>)\n"
                f"Staff: {self.staff_name} ({self.staff_id} | <@{self.staff_id}>)\n"
                f"Type: {TYPES.get(self.infr_type)}\n"
                f"Reason: {self.reason}\n\n"
                f"Expired: {['No', 'Yes'][bool(self.expired)]}"
            )
        )

        return embed
