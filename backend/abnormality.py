import re

def check_status(value: str, ref_range: str) -> dict:
    """Returns a dict with status, math_proof, and limitation."""
    try:
        # Extract numbers from strings safely
        val = float(re.sub(r'[^\d.]', '', value))
    except ValueError:
        return {
            "status": "Unknown", 
            "math_proof": "Could not parse numerical value",
            "limitation": "Value is non-numeric or missing"
        }
    
    if not ref_range or ref_range == "—":
        return {
            "status": "Unknown", 
            "math_proof": "No reference range provided",
            "limitation": "Cannot determine status without a reference range"
        }

    r_str = ref_range.replace(" ", "")
    
    try:
        if r_str.startswith("<"):
            upper = float(re.sub(r'[^\d.]', '', r_str))
            if val > upper:
                return {"status": "Above range", "math_proof": f"{val} > {upper}", "limitation": "Result is higher than the report's upper limit."}
            return {"status": "Within range", "math_proof": f"{val} <= {upper}", "limitation": "Result is within the report's limit."}
            
        elif r_str.startswith(">"):
            lower = float(re.sub(r'[^\d.]', '', r_str))
            if val < lower:
                return {"status": "Below range", "math_proof": f"{val} < {lower}", "limitation": "Result is lower than the report's lower limit."}
            return {"status": "Within range", "math_proof": f"{val} >= {lower}", "limitation": "Result is within the report's limit."}
            
        elif "-" in r_str:
            parts = r_str.split("-")
            if len(parts) == 2:
                lower = float(re.sub(r'[^\d.]', '', parts[0]))
                upper = float(re.sub(r'[^\d.]', '', parts[1]))
                if val < lower:
                    return {"status": "Below range", "math_proof": f"{val} < {lower}", "limitation": "Result is lower than the report's range."}
                if val > upper:
                    return {"status": "Above range", "math_proof": f"{val} > {upper}", "limitation": "Result is higher than the report's range."}
                return {"status": "Within range", "math_proof": f"{lower} <= {val} <= {upper}", "limitation": "Result is within the report's range."}
    except Exception as e:
        pass

    return {"status": "Unknown", "math_proof": "Could not parse reference range format", "limitation": "Unrecognized range format."}