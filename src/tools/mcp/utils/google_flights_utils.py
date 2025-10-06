from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class FlightDetails(BaseModel):
    """Individual flight information"""
    departure_airport_id: Optional[str] = Field(default=None, description="Departure airport IATA code")
    departure_airport_name: Optional[str] = Field(default=None, description="Departure airport name")
    departure_time: Optional[str] = Field(default=None, description="Departure time")
    
    arrival_airport_id: Optional[str] = Field(default=None, description="Arrival airport IATA code")
    arrival_airport_name: Optional[str] = Field(default=None, description="Arrival airport name")
    arrival_time: Optional[str] = Field(default=None, description="Arrival time")
    
    airline: Optional[str] = Field(default=None, description="Airline name")
    flight_number: Optional[str] = Field(default=None, description="Flight number")
    airplane: Optional[str] = Field(default=None, description="Airplane model")
    travel_class: Optional[str] = Field(default=None, description="Travel class (Economy/Business/etc)")
    
    duration: Optional[int] = Field(default=None, description="Duration in minutes")
    legroom: Optional[str] = Field(default=None, description="Legroom info")
    overnight: Optional[bool] = Field(default=None, description="Whether flight is overnight")
    ticket_also_sold_by: Optional[List[str]] = Field(default=None, description="Other airlines selling this ticket")
    extensions: Optional[List[str]] = Field(default=None, description="Additional flight details like Wi-Fi, amenities")
    
    price: Optional[float] = Field(default=None, description="Flight price in USD")
    max_price: Optional[int] = Field(default=None, description="Maximum Flight price in USD")  # ✅ fixed
    
    departure_date: Optional[str] = Field(default=None, description="Departure date YYYY-MM-DD")
    return_date: Optional[str] = Field(default=None, description="Return date YYYY-MM-DD")
    passenger: Optional[int] = Field(default=1, description="Number of passengers")
    
    # Newly required from your error logs:
    total_duration: Optional[int] = Field(default=None, description="Total trip duration in minutes")
    carbon_emissions: Optional[Dict[str, Any]] = Field(default=None, description="Carbon emissions info")
    legs: Optional[List[Dict[str, Any]]] = Field(default=None, description="All flight legs")


def parse_flights(flights_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Parse flight data from SerpAPI response, including all available fields"""
    parsed_flights = []

    for flight_info in flights_data:
        flight_legs = flight_info.get("flights", [])
        if not flight_legs:
            continue

        first_leg = flight_legs[0]

        departure_airport = first_leg.get("departure_airport", {})
        arrival_airport = first_leg.get("arrival_airport", {})
        departure_time = departure_airport.get("time", "")
        arrival_time = arrival_airport.get("time", "")

        parsed_flight = FlightDetails(
            departure_airport_id=departure_airport.get("id"),
            departure_airport_name=departure_airport.get("name"),
            departure_time=departure_time,

            arrival_airport_id=arrival_airport.get("id"),
            arrival_airport_name=arrival_airport.get("name"),
            arrival_time=arrival_time,

            airline=first_leg.get("airline"),
            flight_number=first_leg.get("flight_number"),
            airplane=first_leg.get("airplane"),
            travel_class=first_leg.get("travel_class"),

            duration=first_leg.get("duration"),
            legroom=first_leg.get("legroom"),
            overnight=first_leg.get("overnight"),
            ticket_also_sold_by=first_leg.get("ticket_also_sold_by"),
            extensions=first_leg.get("extensions"),

            price=flight_info.get("price"),

            departure_date=departure_time.split()[0] if departure_time else flight_info.get("departure_date"),
            return_date=flight_info.get("return_date"),
            passenger=flight_info.get("passenger", 1),

            # ✅ new fields
            total_duration=flight_info.get("total_duration"),
            carbon_emissions=flight_info.get("carbon_emissions"),
            legs=flight_info.get("flights")
        )

        parsed_flights.append(parsed_flight.dict())

    return parsed_flights

