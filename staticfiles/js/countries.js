// Countries data with phone codes
const COUNTRIES_DATA = [
    { name: "Afghanistan", code: "AF", phone: "+93" },
    { name: "Albania", code: "AL", phone: "+355" },
    { name: "Algeria", code: "DZ", phone: "+213" },
    { name: "Argentina", code: "AR", phone: "+54" },
    { name: "Australia", code: "AU", phone: "+61" },
    { name: "Austria", code: "AT", phone: "+43" },
    { name: "Bangladesh", code: "BD", phone: "+880" },
    { name: "Belgium", code: "BE", phone: "+32" },
    { name: "Brazil", code: "BR", phone: "+55" },
    { name: "Canada", code: "CA", phone: "+1" },
    { name: "China", code: "CN", phone: "+86" },
    { name: "Denmark", code: "DK", phone: "+45" },
    { name: "Egypt", code: "EG", phone: "+20" },
    { name: "Finland", code: "FI", phone: "+358" },
    { name: "France", code: "FR", phone: "+33" },
    { name: "Germany", code: "DE", phone: "+49" },
    { name: "Greece", code: "GR", phone: "+30" },
    { name: "India", code: "IN", phone: "+91" },
    { name: "Indonesia", code: "ID", phone: "+62" },
    { name: "Ireland", code: "IE", phone: "+353" },
    { name: "Italy", code: "IT", phone: "+39" },
    { name: "Japan", code: "JP", phone: "+81" },
    { name: "Malaysia", code: "MY", phone: "+60" },
    { name: "Mexico", code: "MX", phone: "+52" },
    { name: "Netherlands", code: "NL", phone: "+31" },
    { name: "New Zealand", code: "NZ", phone: "+64" },
    { name: "Norway", code: "NO", phone: "+47" },
    { name: "Pakistan", code: "PK", phone: "+92" },
    { name: "Philippines", code: "PH", phone: "+63" },
    { name: "Poland", code: "PL", phone: "+48" },
    { name: "Portugal", code: "PT", phone: "+351" },
    { name: "Russia", code: "RU", phone: "+7" },
    { name: "Saudi Arabia", code: "SA", phone: "+966" },
    { name: "Singapore", code: "SG", phone: "+65" },
    { name: "South Africa", code: "ZA", phone: "+27" },
    { name: "South Korea", code: "KR", phone: "+82" },
    { name: "Spain", code: "ES", phone: "+34" },
    { name: "Sweden", code: "SE", phone: "+46" },
    { name: "Switzerland", code: "CH", phone: "+41" },
    { name: "Thailand", code: "TH", phone: "+66" },
    { name: "Turkey", code: "TR", phone: "+90" },
    { name: "Ukraine", code: "UA", phone: "+380" },
    { name: "United Arab Emirates", code: "AE", phone: "+971" },
    { name: "United Kingdom", code: "GB", phone: "+44" },
    { name: "United States", code: "US", phone: "+1" },
    { name: "Vietnam", code: "VN", phone: "+84" }
];

// Function to get country by name
function getCountryByName(name) {
    return COUNTRIES_DATA.find(country => 
        country.name.toLowerCase() === name.toLowerCase()
    );
}

// Function to get country by phone code
function getCountryByPhone(phone) {
    return COUNTRIES_DATA.find(country => 
        country.phone === phone
    );
}

// Function to filter countries by search term
function filterCountries(searchTerm) {
    if (!searchTerm) return COUNTRIES_DATA;
    
    const term = searchTerm.toLowerCase();
    return COUNTRIES_DATA.filter(country =>
        country.name.toLowerCase().includes(term) ||
        country.phone.includes(term)
    );
}
