from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.decorators import transactional
from app.db.models.league import LeagueMember
from app.repository.league import LeagueMemberRepository
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class RewardService:
    """
    Servicio para gestionar recompensas de budget según total_points.
    
    Se ejecuta cuando un torneo pasa de "ongoing" → "completed".
    Otorga budget adicional moderado para evitar rosters fáciles de alto nivel.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.member_repo = LeagueMemberRepository(db)
    
    def calculate_bonus_budget(self, total_points: float) -> float:
        """
        Calcula budget adicional según total_points.
        
        Fórmula conservadora (valores moderados):
        - 0-50 pts: +5M
        - 51-100 pts: +10M
        - 101-200 pts: +15M
        - 201-300 pts: +20M
        - 301-500 pts: +25M
        - 501+ pts: +30M (máximo)
        
        Args:
            total_points: Puntos totales acumulados del usuario
        
        Returns:
            float: Budget adicional en millones
        """
        if total_points < 50:
            return 5.0
        elif total_points < 100:
            return 10.0
        elif total_points < 200:
            return 15.0
        elif total_points < 300:
            return 20.0
        elif total_points < 500:
            return 25.0
        else:
            return 30.0  # Cap máximo
    
    @transactional
    async def grant_tournament_rewards(self, tournament_id: int) -> Dict[str, int]:
        """
        Otorga recompensas a TODOS los usuarios al finalizar un torneo.
        
        Se ejecuta cuando un torneo pasa de "ongoing" → "completed".
        
        Args:
            tournament_id: ID del torneo que finalizó
        
        Returns:
            dict: {"members_rewarded": int, "total_budget_granted": float}
        """
        logger.info(f"🎁 Granting tournament rewards for tournament {tournament_id}...")
        
        # Obtener TODOS los league members (de todas las ligas)
        all_members = await self.member_repo.get_all(limit=10000)
        
        members_rewarded = 0
        total_budget_granted = 0.0
        
        for member in all_members:
            try:
                # Calcular bonus según puntos totales
                bonus = self.calculate_bonus_budget(member.total_points)
                new_budget = member.budget + bonus
                
                # Actualizar budget
                await self.member_repo.update(member.id, {"budget": new_budget})
                
                members_rewarded += 1
                total_budget_granted += bonus
                
                logger.info(
                    f"  💰 {member.team_name}: {member.total_points:.2f} pts → "
                    f"+{bonus}M (Budget: {member.budget:.2f}M → {new_budget:.2f}M)"
                )
            
            except Exception as e:
                logger.error(f"  ❌ Error granting reward to member {member.id}: {e}")
                continue
        
        await self.db.flush()
        
        logger.info(
            f"✅ Rewards granted: {members_rewarded} members, "
            f"{total_budget_granted:.2f}M total budget"
        )
        
        return {
            "members_rewarded": members_rewarded,
            "total_budget_granted": total_budget_granted
        }
    
    async def preview_rewards(self) -> Dict[str, list]:
        """
        Preview de recompensas sin aplicarlas (para debugging).
        
        Returns:
            dict: {"rewards_preview": list}
        """
        all_members = await self.member_repo.get_all(limit=100)
        
        preview = []
        for member in all_members[:10]:  # Solo primeros 10 para preview
            bonus = self.calculate_bonus_budget(member.total_points)
            preview.append({
                "team_name": member.team_name,
                "total_points": member.total_points,
                "current_budget": member.budget,
                "bonus": bonus,
                "new_budget": member.budget + bonus
            })
        
        return {"rewards_preview": preview}
