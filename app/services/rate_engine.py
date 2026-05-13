class RateEngine:
    @staticmethod
    def calculate_ranks(rates, volume):
        if not rates:
            return []

        results = []
        for rate in rates:
            total_cost = (rate.base_rate * volume) + rate.surcharges
            results.append({
                'rate': rate,
                'total_cost': total_cost,
                'base_rate': rate.base_rate,
                'surcharges': rate.surcharges,
                'transit_days': rate.transit_days,
                'carrier': rate.carrier_name,
                'frequency': rate.frequency,
                'remarks': rate.remarks
            })

        if not results:
            return []

        # Find min/max for normalization
        costs = [r['total_cost'] for r in results]
        times = [r['transit_days'] for r in results]
        
        min_cost, max_cost = min(costs), max(costs)
        min_time, max_time = min(times), max(times)

        for res in results:
            # Normalize (handle division by zero if all values are same)
            norm_cost = (res['total_cost'] - min_cost) / (max_cost - min_cost) if max_cost > min_cost else 0
            norm_time = (res['transit_days'] - min_time) / (max_time - min_time) if max_time > min_time else 0
            
            # Score (Lower is better for both cost and time, but formula says 0.6*cost + 0.4*time)
            # In logistics excellence, lowest score is usually "Best"
            res['score'] = (0.6 * norm_cost) + (0.4 * norm_time)
            res['tag'] = None

        # Sort by cost (Cheapest)
        cheapest = min(results, key=lambda x: x['total_cost'])
        # Sort by days (Fastest)
        fastest = min(results, key=lambda x: x['transit_days'])
        # Sort by score (Best)
        recommended = min(results, key=lambda x: x['score'])

        # Assign tags
        recommended['tag'] = 'Recommended'
        cheapest['tag'] = 'Cheapest' if cheapest['tag'] is None else recommended['tag'] # Prioritize recommended
        fastest['tag'] = 'Fastest' if fastest['tag'] is None else recommended['tag']

        # Special casing: if same item is multiple things, ensure Recommended wins the main display
        # But we'll return the top 3 items that represent these categories
        
        # Unique identifying to avoid duplicates if one nvocc fits all
        top_picks = []
        seen_ids = set()
        
        for pick in [recommended, cheapest, fastest]:
            if pick['rate'].id not in seen_ids:
                # Add tag info specifically for the UI comparison
                if pick == recommended: pick['ui_tag'] = 'Recommended'
                elif pick == cheapest: pick['ui_tag'] = 'Cheapest'
                elif pick == fastest: pick['ui_tag'] = 'Fastest'
                
                top_picks.append(pick)
                seen_ids.add(pick['rate'].id)
            else:
                # If already added, maybe append the tag?
                for p in top_picks:
                    if p['rate'].id == pick['rate'].id:
                        if pick == recommended: p['ui_tag'] = 'Recommended' # Recommended overrides

        return top_picks
