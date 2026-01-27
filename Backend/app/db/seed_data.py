from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.service.user import UserService
from app.service.professional import TeamService, PlayerService
from app.service.league import LeagueService, LeagueMemberService, RosterService
from app.service.match import MatchService, PlayerMatchStatsService
from app.db.models.user import UserRole
from app.db.models.professional import Region, PlayerRole
from datetime import datetime, timedelta
import random

def seed_data():
    db = SessionLocal()
    try:
        user_service = UserService(db)
        team_service = TeamService(db)
        player_service = PlayerService(db)
        league_service = LeagueService(db)
        member_service = LeagueMemberService(db)
        roster_service = RosterService(db)
        match_service = MatchService(db)
        stats_service = PlayerMatchStatsService(db)

        # 1. Seed Users
        print("Seeding Users...")
        users = []
        try:
            admin = user_service.create(email="admin@fantasy.com", username="admin", password="adminpassword123", role="admin")
            users.append(admin)
        except Exception: pass # Skip if exists

        for i in range(1, 6):
            try:
                u = user_service.create(email=f"user{i}@test.com", username=f"user_{i}", password="testpassword123")
                users.append(u)
            except Exception: pass

        # 2. Seed Teams
        print("Seeding Teams...")
        team_data = [
            {"name": "Fnatic", "region": "EMEA", "logo_url": "https://example.com/fnatic.png"},
            {"name": "Sentinels", "region": "Americas", "logo_url": "https://example.com/sentinels.png"},
            {"name": "Paper Rex", "region": "Pacific", "logo_url": "https://example.com/prx.png"},
            {"name": "LOUD", "region": "Americas", "logo_url": "https://example.com/loud.png"},
            {"name": "Team Liquid", "region": "EMEA", "logo_url": "https://example.com/liquid.png"}
        ]
        teams = []
        for t in team_data:
            try:
                team = team_service.create(name=t["name"], region=t["region"], logo_url=t["logo_url"])
                teams.append(team)
            except Exception:
                team = team_service.repo.get_by_name(t["name"])
                if team: teams.append(team)

        # 3. Seed Players
        print("Seeding Players...")
        roles = ["Duelist", "Initiator", "Controller", "Sentinel", "Flex"]
        for team in teams:
            for i in range(5):
                try:
                    player_service.create(
                        name=f"{team.name}_Player_{i+1}",
                        role=roles[i % 5],
                        region=team.region,
                        team_id=team.id,
                        current_price=random.uniform(5.0, 20.0),
                        base_price=10.0,
                        points=0.0
                    )
                except Exception: pass

        # 4. Seed Leagues
        print("Seeding Leagues...")
        try:
            league = league_service.create(name="Pro Valorant League", admin_user_id=users[0].id)
            
            # Join users to league
            for user in users:
                try:
                    member = member_service.join_league(
                        league_id=league.id,
                        user_id=user.id,
                        team_name=f"{user.username}'s Squad",
                        selected_team_id=random.choice(teams).id
                    )
                    
                    # Add some players to roster
                    all_players = player_service.get_all()
                    sample_players = random.sample(all_players, min(len(all_players), 5))
                    for p in sample_players:
                        try:
                            roster_service.add_player(
                                league_member_id=member.id,
                                player_id=p.id,
                                is_starter=True
                            )
                        except Exception: pass
                except Exception: pass
        except Exception: pass

        # 5. Seed Matches
        print("Seeding Matches...")
        for i in range(5):
            try:
                t1, t2 = random.sample(teams, 2)
                match = match_service.create(
                    vlr_match_id=f"vlr_{random.randint(10000, 99999)}",
                    date=datetime.utcnow() - timedelta(days=i),
                    status="completed",
                    tournament_name="VCT Champions",
                    team_a_id=t1.id,
                    team_b_id=t2.id,
                    score_team_a=2,
                    score_team_b=1
                )
                
                # Seed stats for players in this match
                t1_players = player_service.get_by_team(t1.id)
                t2_players = player_service.get_by_team(t2.id)
                
                for p in t1_players + t2_players:
                    try:
                        stats_service.create(
                            match_id=match.id,
                            player_id=p.id,
                            agent="Jett",
                            kills=random.randint(10, 30),
                            death=random.randint(10, 25),
                            assists=random.randint(2, 15),
                            acs=random.uniform(150, 350),
                            rating=random.uniform(0.8, 1.5)
                        )
                    except Exception: pass
            except Exception: pass

        print("Seeding completed successfully!")

    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
