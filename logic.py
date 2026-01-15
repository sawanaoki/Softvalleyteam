import math

def create_matches(males_count, females_count, num_matches, mode="balanced", late_males=0, late_females=0, late_match_start=1):
    """
    Generate match schedule based on the number of players and matches.
    """
    if mode == "random":
        # 簡易化のため一旦ランダムモードは途中参加非対応（既存の引数で呼び出し）
        return create_random_matches(males_count, females_count, num_matches)
    elif mode == "fixed_pairs":
        # 簡易化のため一旦ペア固定モードも途中参加非対応
        return create_fixed_pair_matches(males_count, females_count, num_matches)
        
    # Default Balanced Mode
    base_males = int(males_count)
    base_females = int(females_count)
    extra_males = int(late_males)
    extra_females = int(late_females)
    total_males = base_males + extra_males
    total_females = base_females + extra_females
    matches_target = int(num_matches)
    start_match_idx = int(late_match_start) - 1

    if base_males < 4 or base_females < 4:
        raise ValueError('初期メンバーとして男性4名以上、女性4名以上を入力してください。')
    
    if matches_target < 1:
        raise ValueError('試合数を1以上で入力してください。')

    if total_males > 1000 or total_females > 1000 or matches_target > 1000:
       raise ValueError('人数または試合数が大きすぎます。')

    # Status tracking
    male_play_count = [0] * total_males
    female_play_count = [0] * total_females
    male_last_played = [-2] * total_males
    female_last_played = [-2] * total_females
    
    # Each player's start match index (0-indexed)
    male_start_indices = [0] * base_males + [start_match_idx] * extra_males
    female_start_indices = [0] * base_females + [start_match_idx] * extra_females

    # Pair history tracking
    male_pair_history = [[0] * total_males for _ in range(total_males)]
    female_pair_history = [[0] * total_females for _ in range(total_females)]

    matches = []

    for match_num in range(matches_target):
        # 1. Select players
        # Priority: play_count * 100 + (match_num - last_played)
        # For late joiners who haven't arrived yet, set priority very high
        
        available_males = []
        for i in range(total_males):
            if match_num < male_start_indices[i]:
                priority = 1000000 # Joined later
            else:
                priority = male_play_count[i] * 100 + (match_num - male_last_played[i])
            
            available_males.append({
                'id': i,
                'play_count': male_play_count[i],
                'last_played': male_last_played[i],
                'priority': priority
            })
        
        available_males.sort(key=lambda x: x['priority'])
        if available_males[3]['priority'] >= 1000000:
             raise ValueError(f'第{match_num + 1}試合時点で参加可能な男性が不足しています（最低4名必要）。')
        selected_males_indices = [m['id'] for m in available_males[:4]]
        
        available_females = []
        for i in range(total_females):
            if match_num < female_start_indices[i]:
                priority = 1000000
            else:
                priority = female_play_count[i] * 100 + (match_num - female_last_played[i])
                
            available_females.append({
                'id': i,
                'play_count': female_play_count[i],
                'last_played': female_last_played[i],
                'priority': priority
            })
            
        available_females.sort(key=lambda x: x['priority'])
        if available_females[3]['priority'] >= 1000000:
             raise ValueError(f'第{match_num + 1}試合時点で参加可能な女性が不足しています（最低4名必要）。')
        selected_females_indices = [f['id'] for f in available_females[:4]]

        # 2. Find best team split
        best_teams = find_best_team_split(
            selected_males_indices, 
            selected_females_indices, 
            male_pair_history, 
            female_pair_history
        )

        # 3. Update stats
        for idx in selected_males_indices:
            male_play_count[idx] += 1
            male_last_played[idx] = match_num
            
        for idx in selected_females_indices:
            female_play_count[idx] += 1
            female_last_played[idx] = match_num

        # Update pair history using the best split
        # Team 1 Males
        update_pair_history(best_teams['team1']['males'], male_pair_history)
        # Team 2 Males
        update_pair_history(best_teams['team2']['males'], male_pair_history)
        # Team 1 Females
        update_pair_history(best_teams['team1']['females'], female_pair_history)
        # Team 2 Females
        update_pair_history(best_teams['team2']['females'], female_pair_history)

        # 4. Determine waiting members
        waiting_males = [i + 1 for i in range(total_males) if i not in selected_males_indices and match_num >= male_start_indices[i]]
        waiting_females = [i + 1 for i in range(total_females) if i not in selected_females_indices and match_num >= female_start_indices[i]]

        # Convert 0-indexed IDs to 1-indexed for display
        team1_display = {
            'males': [x + 1 for x in best_teams['team1']['males']],
            'females': [x + 1 for x in best_teams['team1']['females']]
        }
        team2_display = {
            'males': [x + 1 for x in best_teams['team2']['males']],
            'females': [x + 1 for x in best_teams['team2']['females']]
        }

        matches.append({
            'match_number': match_num + 1,
            'team1': team1_display,
            'team2': team2_display,
            'waiting': {
                'males': waiting_males,
                'females': waiting_females
            }
        })

    return matches


def has_same_id_collision(team_males, team_females):
    """
    Check if there is a collision where Male N and Female N are on the same team.
    team_males: list of 0-based indices
    team_females: list of 0-based indices
    """
    return not set(team_males).isdisjoint(set(team_females))


def create_random_matches(males_count, females_count, num_matches):
    """
    Generate completely random matches.
    """
    import random
    males = int(males_count)
    females = int(females_count)
    
    matches = []
    
    # 0-indexed lists of all players
    all_males = list(range(males))
    all_females = list(range(females))
    
    for match_num in range(num_matches):
        team1 = {}
        team2 = {}
        waiting_males = []
        waiting_females = []
        
        # Try to find a configuration without ID collisions
        # Retry up to 20 times, then accept whatever to avoid infinite loop
        found_valid = False
        
        for _ in range(20):
            random.shuffle(all_males)
            random.shuffle(all_females)
            
            selected_males = all_males[:4]
            selected_females = all_females[:4]
            
            # Temporary teams check
            t1_m = [selected_males[0], selected_males[1]]
            t1_f = [selected_females[0], selected_females[1]]
            t2_m = [selected_males[2], selected_males[3]]
            t2_f = [selected_females[2], selected_females[3]]
            
            if not has_same_id_collision(t1_m, t1_f) and not has_same_id_collision(t2_m, t2_f):
                found_valid = True
                break
        
        # If not found valid after retries, use the last shuffled result
        
        selected_males = all_males[:4]
        selected_females = all_females[:4]
        
        waiting_males = [m + 1 for m in all_males[4:]]
        waiting_females = [f + 1 for f in all_females[4:]]
        
        team1 = {
            'males': [selected_males[0] + 1, selected_males[1] + 1],
            'females': [selected_females[0] + 1, selected_females[1] + 1]
        }
        
        team2 = {
            'males': [selected_males[2] + 1, selected_males[3] + 1],
            'females': [selected_females[2] + 1, selected_females[3] + 1]
        }
        
        # Sort for better display
        team1['males'].sort()
        team1['females'].sort()
        team2['males'].sort()
        team2['females'].sort()
        waiting_males.sort()
        waiting_females.sort()
        
        matches.append({
            'match_number': match_num + 1,
            'team1': team1,
            'team2': team2,
            'waiting': {
                'males': waiting_males,
                'females': waiting_females
            }
        })
        
    return matches


def create_fixed_pair_matches(males_count, females_count, num_matches):
    """
    Generate matches where pairs are fixed (e.g., M1-M2, M3-M4).
    """
    import math
    
    males = int(males_count)
    females = int(females_count)
    matches_target = int(num_matches)
    
    # Define Pairs (0-indexed)
    # Pair i: (2*i, 2*i + 1)
    
    male_units = []
    for i in range(0, males, 2):
        if i + 1 < males:
            male_units.append([i, i+1])
        else:
            male_units.append([i]) # Solo
            
    female_units = []
    for i in range(0, females, 2):
        if i + 1 < females:
            female_units.append([i, i+1])
        else:
            female_units.append([i])
            
    # Track plays per UNIT
    male_unit_plays = [0] * len(male_units)
    female_unit_plays = [0] * len(female_units)
    
    matches = []
    
    for match_num in range(matches_target):
        # 1. Sort units by play count
        sorted_m_units = sorted(range(len(male_units)), key=lambda k: male_unit_plays[k])
        sorted_f_units = sorted(range(len(female_units)), key=lambda k: female_unit_plays[k])
        
        selected_m_unit_indices = sorted_m_units[:2]
        selected_f_unit_indices = sorted_f_units[:2]
        
        # Update play stats
        for u_idx in selected_m_unit_indices:
            male_unit_plays[u_idx] += 1
        for u_idx in selected_f_unit_indices:
            female_unit_plays[u_idx] += 1
            
        # Form teams candidates
        m_u1 = male_units[selected_m_unit_indices[0]]
        m_u2 = male_units[selected_m_unit_indices[1]]
        f_u1 = female_units[selected_f_unit_indices[0]]
        f_u2 = female_units[selected_f_unit_indices[1]]
        
        # Check collision for standard pairing: T1=(M1, F1), T2=(M2, F2)
        collision_std = has_same_id_collision(m_u1, f_u1) or has_same_id_collision(m_u2, f_u2)
        
        # Check collision for swapped pairing: T1=(M1, F2), T2=(M2, F1)
        collision_swap = has_same_id_collision(m_u1, f_u2) or has_same_id_collision(m_u2, f_u1)
        
        # Prefer swap if it resolves collision
        if collision_std and not collision_swap:
            # Swap
            final_f_u1 = f_u2
            final_f_u2 = f_u1
        else:
            final_f_u1 = f_u1
            final_f_u2 = f_u2
        
        # Convert to 1-based
        team1 = {
            'males': [x + 1 for x in m_u1],
            'females': [x + 1 for x in final_f_u1]
        }
        team2 = {
            'males': [x + 1 for x in m_u2],
            'females': [x + 1 for x in final_f_u2]
        }
        
        # Waiting
        selected_m_flat = m_u1 + m_u2
        selected_f_flat = f_u1 + f_u2 # Original selection sets are same regardless of swap
        
        waiting_males = [i + 1 for i in range(males) if i not in selected_m_flat]
        waiting_females = [i + 1 for i in range(females) if i not in selected_f_flat]
        
        matches.append({
            'match_number': match_num + 1,
            'team1': team1,
            'team2': team2,
            'waiting': {
                'males': waiting_males,
                'females': waiting_females
            }
        })
        
    return matches


def find_best_team_split(males, females, male_history, female_history):
    """
    Find the split of 4 players into 2 pairs (2 vs 2) that minimizes repeat pairs.
    """
    best_score = float('inf')
    best_teams = None

    # All ways to split 4 males into 2 pairs:
    # 0,1 vs 2,3
    # 0,2 vs 1,3
    # 0,3 vs 1,2
    # males list has 4 indices
    male_splits = [
        [[males[0], males[1]], [males[2], males[3]]],
        [[males[0], males[2]], [males[1], males[3]]],
        [[males[0], males[3]], [males[1], males[2]]]
    ]

    female_splits = [
        [[females[0], females[1]], [females[2], females[3]]],
        [[females[0], females[2]], [females[1], females[3]]],
        [[females[0], females[3]], [females[1], females[2]]]
    ]

    for m_split in male_splits:
        for f_split in female_splits:
            # Option 1: T1(M1, F1), T2(M2, F2)
            score1 = (
                male_history[m_split[0][0]][m_split[0][1]] +
                male_history[m_split[1][0]][m_split[1][1]] +
                female_history[f_split[0][0]][f_split[0][1]] +
                female_history[f_split[1][0]][f_split[1][1]]
            )
            
            if has_same_id_collision(m_split[0], f_split[0]):
                score1 += 10000
            if has_same_id_collision(m_split[1], f_split[1]):
                score1 += 10000
                
            if score1 < best_score:
                best_score = score1
                best_teams = {
                    'team1': {'males': m_split[0], 'females': f_split[0]},
                    'team2': {'males': m_split[1], 'females': f_split[1]}
                }

            # Option 2: T1(M1, F2), T2(M2, F1)
            # History score is same for pairs, but team composition is different?
            # Actually, "score" in original code was just sum of PAIR history.
            # Does team composition matter for pair history?
            # Original code: score = male_pair_hist + female_pair_hist.
            # It didn't account for mixed history (M-F history).
            # So the base score is IDENTICAL for Option 1 and Option 2.
            # But the PENALTY might differ.
            
            score2 = score1 # Base score is same
            
            # Reset penalty logic for Option 2
            # Remove any penalty added to score1? No, score1 is modified.
            # Re-calculate clean score from scratch is safer.
            
            clean_score = (
                male_history[m_split[0][0]][m_split[0][1]] +
                male_history[m_split[1][0]][m_split[1][1]] +
                female_history[f_split[0][0]][f_split[0][1]] +
                female_history[f_split[1][0]][f_split[1][1]]
            )
            
            score2 = clean_score
            if has_same_id_collision(m_split[0], f_split[1]):
                score2 += 10000
            if has_same_id_collision(m_split[1], f_split[0]):
                score2 += 10000
                
            if score2 < best_score:
                best_score = score2
                best_teams = {
                    'team1': {'males': m_split[0], 'females': f_split[1]},
                    'team2': {'males': m_split[1], 'females': f_split[0]}
                }
    
    return best_teams


def update_pair_history(pair, history):
    p1, p2 = pair
    history[p1][p2] += 1
    history[p2][p1] += 1


def get_play_stats_snapshot(matches, current_match_index, total_males, total_females):
    """
    Calculate play stats up to the current match index.
    """
    if not matches:
        return None
    
    male_counts = [0] * total_males
    female_counts = [0] * total_females

    # Check up to current_match_index (inclusive)
    limit = min(current_match_index + 1, len(matches))
    
    for i in range(limit):
        match = matches[i]
        
        # IDs in match are 1-based, convert to 0-based for array indexing
        for mid in match['team1']['males']:
            if 1 <= mid <= total_males:
                male_counts[mid - 1] += 1
        for mid in match['team2']['males']:
            if 1 <= mid <= total_males:
                male_counts[mid - 1] += 1
                
        for fid in match['team1']['females']:
            if 1 <= fid <= total_females:
                female_counts[fid - 1] += 1
        for fid in match['team2']['females']:
            if 1 <= fid <= total_females:
                female_counts[fid - 1] += 1
                
    return {'male_counts': male_counts, 'female_counts': female_counts}
