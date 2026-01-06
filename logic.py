import math

def create_matches(males_count, females_count, num_matches):
    """
    Generate match schedule based on the number of players and matches.
    Ported from React implementation.
    """
    males = int(males_count)
    females = int(females_count)
    matches_target = int(num_matches)

    if males < 4 or females < 4:
        raise ValueError('男性4名以上、女性4名以上を入力してください。')
    
    if matches_target < 1:
        raise ValueError('試合数を1以上で入力してください。')

    if males > 1000 or females > 1000 or matches_target > 1000:
       raise ValueError('人数または試合数が大きすぎます。')

    # Status tracking
    # 0-indexed internally, but IDs will be 1-indexed for display
    male_play_count = [0] * males
    female_play_count = [0] * females
    male_last_played = [-2] * males
    female_last_played = [-2] * females

    # Pair history tracking (1-indexed keys as in original code logic, or simplified to 0-indexed)
    # Using 0-indexed for Python implementation simplicity, will convert to 1-based for IDs later.
    male_pair_history = [[0] * males for _ in range(males)]
    female_pair_history = [[0] * females for _ in range(females)]

    matches = []

    for match_num in range(matches_target):
        # 1. Select players
        # Priority: play_count * 100 + (match_num - last_played)
        # Smaller priority is better
        
        available_males = []
        for i in range(males):
            priority = male_play_count[i] * 100 + (match_num - male_last_played[i])
            available_males.append({
                'id': i,
                'play_count': male_play_count[i],
                'last_played': male_last_played[i],
                'priority': priority
            })
        
        # Sort by priority (asc)
        available_males.sort(key=lambda x: x['priority'])
        selected_males_indices = [m['id'] for m in available_males[:4]]
        
        available_females = []
        for i in range(females):
            priority = female_play_count[i] * 100 + (match_num - female_last_played[i])
            available_females.append({
                'id': i,
                'play_count': female_play_count[i],
                'last_played': female_last_played[i],
                'priority': priority
            })
            
        available_females.sort(key=lambda x: x['priority'])
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
        waiting_males = [i + 1 for i in range(males) if i not in selected_males_indices]
        waiting_females = [i + 1 for i in range(females) if i not in selected_females_indices]

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
            # Score = sum of history counts for all pairs in this configuration
            # m_split[0] is pair 1 (team 1 males), m_split[1] is pair 2 (team 2 males)
            score = (
                male_history[m_split[0][0]][m_split[0][1]] +
                male_history[m_split[1][0]][m_split[1][1]] +
                female_history[f_split[0][0]][f_split[0][1]] +
                female_history[f_split[1][0]][f_split[1][1]]
            )

            if score < best_score:
                best_score = score
                best_teams = {
                    'team1': {'males': m_split[0], 'females': f_split[0]},
                    'team2': {'males': m_split[1], 'females': f_split[1]}
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
