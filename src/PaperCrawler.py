class Url(object):
    def __init__(self, url, title, ref_num, depth):
        self.url = url
        self.title = title
        self.ref_num = ref_num
        self.depth = depth
    
    def __lt__(self, other):
        return self.ref_num > other.ref_num
    
    def __gt__(self, other):
        return self.ref_num < other.ref_num
        
    def __eq__(self, other):
        return self.ref_num == other.ref_num


class Paper(Url):
    def __init__(self, url, title, ref_num, abstract, depth=-1):
        super(Paper, self).__init__(url, title, ref_num, depth)
        self.abstract = abstract
        
        
class Url_pool(object):
    def __init__(self):
        from heapq import heapify
        self.url_his = set()
        self.title_his = set()
        self.urls = []
        heapify(self.urls)
    
    def append_url(self, url):
        from heapq import heappush
        import re
        
        pun = "[\s+\.\!\/_,$%^*(+\"\']+|[+——！:‐-，。？、~@#￥%……&*（）]+"
        if re.sub(pun, "", url.title) in self.title_his:
            pass
        elif url.url in self.url_his:
            pass
        else:
            self.url_his.add(url.url)
            self.title_his.add(re.sub(pun, "", url.title))
            heappush(self.urls, url)
    
    def get_url(self):
        from heapq import heappop
        if len(self.urls) > 0:
            return heappop(self.urls)
        else:
            return None

class PaperCrawler(object):
    def __init__(self, init_url="https://xueshu.baidu.com/usercenter/paper/show?paperid=3821a90f58762386e257eb4e6fa11f79", 
                 basic_url="https://xueshu.baidu.com", max_depth=5, tot_papers=10, wait_time=2):
        self.init_url = init_url
        self.basic_url = basic_url
        self.max_depth = max_depth
        self.tot_papers = tot_papers
        self.wait_time = wait_time
        
        self.url_pool = Url_pool()
        self.papers = []
        
    def crawl(self):
        cur_depth = 0
        self.papers.append(self.parse_url(self.init_url, cur_depth))
        while len(self.papers) < self.tot_papers:
            url = self.url_pool.get_url()
            cur_depth = url.depth
            self.papers.append(self.parse_url(url.url, cur_depth))
        self.store()
    
    def parse_url(self, url, depth):
        from bs4 import BeautifulSoup
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options

        options = Options()
        options.add_argument('--headless')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])

        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(self.wait_time)
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        main_info = soup.find(name='div', attrs={"class":"main-info"})
        title = main_info.find(name='h3').text.strip()
        print(f"Crawling  {len(self.papers)+1}/{self.tot_papers}----------Title:  {title}")
        try:
            abstract = main_info.find(name='p', attrs={"class":"abstract"}).text.strip()
        except Exception as e:
            abstract = "No Abstract"
        ref_num = main_info.find(name='p', attrs={"class":"ref-wr-num"}).text.strip()
        if ref_num.endswith("万"):
            ref_num = int(float(ref_num[:-1])*10000)
        else:
            ref_num = int(ref_num)
        paper = Paper(url, title, ref_num, abstract)
        
        rel_lists = soup.find(name='ul', attrs={"class":"related_lists"})
        if rel_lists and depth < self.max_depth:
            rel_urls = rel_lists.find_all(name='li')
            for rel_url in rel_urls:
                url = self.basic_url + rel_url.find(name='p', attrs={"class":"rel_title"}).find(name="a").get('href')
                title = rel_url.find(name='p', attrs={"class":"rel_title"}).find(name="a").text.strip()
                try:
                    ref_num = rel_url.find(name='div', attrs={"class":"sc_info"}).find(name="a").text.strip()
                    if ref_num.endswith("万"):
                        ref_num = int(float(ref_num[:-1])*10000)
                    else:
                        ref_num = int(ref_num)
                except Exception as e:
                    ref_num = 0
                self.url_pool.append_url(Url(url, title, ref_num, depth+1))     
    
        driver.quit()
        
        return paper
    
    def store(self, filename='result.txt', encoding='utf-8'):
        self.papers.sort()
        with open(filename, 'w', errors="ignore") as f:
            for paper in self.papers:
                f.write(f"Title:  {paper.title}\n")
                f.write(f"Abstract:  {paper.abstract}\n")
                f.write(f"Ref_num:  {paper.ref_num}\n")
                f.write(f"URL:  {paper.url}\n")
                f.write("\n")


if  __name__  == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--max-depth", type=int, default=5, help="max_depth")
    parser.add_argument("-t", "--tot-papers", type=int, default=10, help="tot_papers")
    parser.add_argument("-w", "--wait-time", type=int, default=2, help="wait_time")
    parser.add_argument("-i", "--init-url", type=str, default="https://xueshu.baidu.com/usercenter/paper/show?paperid=3821a90f58762386e257eb4e6fa11f79"
    , help="init_url")
    args = parser.parse_args()
    
    crawler = PaperCrawler(init_url=args.init_url, max_depth=args.max_depth, tot_papers=args.tot_papers, wait_time=args.wait_time)
    crawler.crawl()