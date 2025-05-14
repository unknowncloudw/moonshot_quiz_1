from bs4 import BeautifulSoup
import json
import re
from tqdm import tqdm
import os
def process_curly_brackets(text,start):
    #处理花括号（模板），考虑嵌套情况
    end = text.find('}}',start)
    if end == -1:
        return text[:start] + text[start+2:]
    if text[start:].startswith('{{lang') or text[start:].startswith('{{Lang'):
        link = text[start+2:end]
        new_text = text[:start] +link.split('|')[0]+ text[end+2:]

    else:
        for i in range(start+2, len(text)):
            if text[i:i+2] == '{{':
                text=process_curly_brackets(text, i)
                            
            elif text[i:i+2] == '}}':
                end = i
                break
        new_text = text[:start] + text[end+2:]

    return new_text


def process_square_brackets(text,start):
    #处理方括号（链接）。考虑嵌套情况。
    end = text.find(']]',start)
    if end == -1:
        return text[:start] + text[start+2:]
    if text[start:].startswith('[[File') or text[start:].startswith('[[Image') or text[start:].startswith('[[Wikipedia') or text[start:].startswith('[[Category'):
        for i in range(start+2, len(text)):
            if text[i:i+2] == ']]':
                end = i
                break
            elif text[i:i+2] == '[[':
                text=process_square_brackets(text, i)
        new_text = text[:start] + text[end+2:]
    else:
        link = text[start+2:end]
        new_text = text[:start] +link.split('|')[0]+ text[end+2:]


    return new_text


def wash_text(text):
    washed_text = []
    pattern_notation = r'<\!--[\s\S]*?-->'
    pattern_table = r':?{\|[\s\S]*?\|}'
    pattern_tag = r'<([a-zA-Z0-9_-]{1,20})[\s\S]*?</\1>'

    #去除所有注释 <!-- ... -->
    while re.search(pattern_notation, text):
        text = re.sub(pattern_notation, '', text)

    #去除所有表格 {|...|}
    while re.search(pattern_table, text):
        text = re.sub(pattern_table, '', text)
    
    #去除所有标签 <tag>...</tag>
    while re.search(pattern_tag, text):
        text = re.sub(pattern_tag, '', text)



    #处理可能存在嵌套的模板 {{...}}
    while text.find('{{') != -1:
        start = text.find('{{')
        text=process_curly_brackets(text, start)

    #处理可能存在嵌套的链接 [[...]]
    while text.find('[[') != -1:
        start = text.find('[[')
        text=process_square_brackets(text, start)

    #分行
    for line in text.split('\n'):

        if line.startswith('==') and line.endswith('=='):
            # 去除标题
            continue

        if line.startswith('*'):
            # 去除列表
            continue

        #去除强调
        line=line.replace('\'\'\'','')

        if line == '':
            # 去除空行
            continue

        if len(line)<=20:
            # 去除行长度小于10的行
            continue
        washed_text.append(line)


    return washed_text


if __name__ == '__main__':

    # 读取索引文件
    for file in os.listdir('data'):
        if '.xml' in file:
            file_path = os.path.join('data', file)

            print(f"Processing file: {file_path}")
            # 读取xml文件
            with open(file_path,'r',encoding='utf-8') as f:
                xml = f.read()

            #使用bs4读取整个xml文件消耗内存较大，因此将xml文件分割成多个page，并逐个解析
            pages = []
            for match in re.finditer(r'<page.*?>.*?</page>', xml, re.DOTALL):
                page = match.group(0)
                pages.append(page)

            print(f"Total pages extracted: {len(pages)}")

            # 逐个解析page，并将解析结果写入jsonl文件
            for i in tqdm(range(len(pages))):
                page=pages[i]
                soup = BeautifulSoup(page, 'xml')
                title = soup.find('title').text
                text = soup.find('text').text
                text_list = wash_text(text)
                with open(f'./washed_text.jsonl','a',encoding='utf-8') as f:
                    for line in text_list:
                        f.write(json.dumps({'text':line,'meta':{'title':title}},ensure_ascii=False)+'\n')