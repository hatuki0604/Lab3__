# Mock Dataset for Vietnamese Literature

BOOKS_DATASET = [
    {
        "title": "Chí Phèo",
        "author": "Nam Cao",
        "year": 1941,
        "genre": "truyện ngắn",
        "region": "Việt Nam",
        "summary": "Một tác phẩm hiện thực xuất sắc nói về cuộc đời của Chí Phèo - một người nông dân lương thiện bị tha hóa và cướp đi nhân hình lẫn nhân tính bởi xã hội phong kiến thực dân."
    },
    {
        "title": "Lão Hạc",
        "author": "Nam Cao",
        "year": 1943,
        "genre": "truyện ngắn",
        "region": "Việt Nam",
        "summary": "Truyện ngắn đầy cảm động về số phận bi thảm của một người nông dân nghèo phải bán con chó vàng yêu quý và chọn cái chết bằng bả chó để giữ lại mảnh đất cho con trai."
    },
    {
        "title": "Đời thừa",
        "author": "Nam Cao",
        "year": 1943,
        "genre": "truyện ngắn",
        "region": "Việt Nam",
        "summary": "Tác phẩm phản ánh tấn bi kịch tinh thần sâu sắc của người trí thức nghèo Hộ, khao khát viết nên tác phẩm lớn nhưng bị cơm áo gạo tiền ghì sát đất."
    },
    {
        "title": "Sống chết mặc bay",
        "author": "Phạm Duy Tốn",
        "year": 1918,
        "genre": "truyện ngắn",
        "region": "Việt Nam",
        "summary": "Tác phẩm hiện thực phê phán cảnh quan lại ăn chơi tổ tôm trong khi đê vỡ, nhân dân lầm than chìm trong lũ lụt."
    },
    {
        "title": "Tinh thần thể dục",
        "author": "Nguyễn Công Hoan",
        "year": 1939,
        "genre": "truyện ngắn",
        "region": "Việt Nam",
        "summary": "Một thiên truyện ngắn trào phúng sâu sắc châm biếm chính sách thể dục thể thao bịp bợm của thực dân Pháp bắt ép nhân dân tham gia."
    },
    {
        "title": "Vợ nhặt",
        "author": "Kim Lân",
        "year": 1962,
        "genre": "truyện ngắn",
        "region": "Việt Nam",
        "summary": "Tác phẩm viết về nạn đói khủng khiếp năm 1945, qua đó thể hiện tình người ấm áp, khát vọng sống và niềm tin vào tương lai của những con người nghèo khổ."
    },
    {
        "title": "Làng",
        "author": "Kim Lân",
        "year": 1948,
        "genre": "truyện ngắn",
        "region": "Việt Nam",
        "summary": "Tác phẩm thể hiện lòng yêu làng thống nhất và hòa quyện sâu sắc với lòng yêu nước, tinh thần kháng chiến của người nông dân tản cư."
    },
    {
        "title": "Chiếc lược ngà",
        "author": "Nguyễn Quang Sáng",
        "year": 1966,
        "genre": "truyện ngắn",
        "region": "Việt Nam",
        "summary": "Câu chuyện cảm động về tình cha con thiêng liêng, bất diệt giữa bé Thu và ông Sáu trong hoàn cảnh chiến tranh khốc liệt."
    },
    {
        "title": "Rừng xà nu",
        "author": "Nguyễn Trung Thành",
        "year": 1965,
        "genre": "truyện ngắn",
        "region": "Việt Nam",
        "summary": "Bản anh hùng ca về cuộc chiến đấu kiên cường của dân làng Xô Man (Tây Nguyên) thông qua cuộc đời của Tnú và sức sống bất diệt của rừng cây xà nu."
    },
    {
        "title": "Vợ chồng A Phủ",
        "author": "Tô Hoài",
        "year": 1952,
        "genre": "truyện ngắn",
        "region": "Việt Nam",
        "summary": "Tác phẩm phản ánh cuộc sống tủi cực, áp bức dã man của thống lý Pá Tra đối với Mị và A Phủ ở vùng núi cao Tây Bắc, đồng thời ca ngợi sức sống tiềm tàng và khát vọng tự do của họ."
    }
]

def search_local_db(query: str) -> list:
    """
    Tầng 1: Tìm kiếm trong database mock nội bộ.
    Tìm kiếm không phân biệt hoa thường theo tên tác phẩm hoặc tác giả.
    """
    query_lower = query.lower().strip()
    results = []
    
    for book in BOOKS_DATASET:
        if query_lower in book["title"].lower() or query_lower in book["author"].lower():
            results.append(book)
            
    return results
