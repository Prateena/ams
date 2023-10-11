import math

from django import template

register = template.Library() 

@register.filter(name='pages') 
def pages(paginator, current_page, max_pages=9):
	return get_rage(num_pages=paginator.num_pages, current_page=current_page.number, max_pages=max_pages)

def get_rage(num_pages, current_page, max_pages):
	pages_list = []
	max_pages = max_pages
	num_pages = num_pages
	center_first = math.floor((1+max_pages)/2)

	# analyzing start and end pages.
	start = 0
	end = 0
	if num_pages <=  max_pages:
		start = 1
		end = num_pages
	elif current_page <= center_first:
		start = 1
		end = start + max_pages - 1
	else:
		start = current_page - center_first + 1
		end = start + max_pages - 1

		if(end > num_pages):
			end = num_pages
			start = end - max_pages + 1

	# analyzing jump pages for starting pages
	hasFirstPage = True
	hasCenterFirstPage = True
	if not 1 in range(start, end+1):
		hasFirstPage = False
		firstCenter = (start+1) // 2
		if firstCenter <= 2:
			hasCenterFirstPage = True
		else: 
			hasCenterFirstPage = False

	# analyzing jump pages for ending pages
	hasLastPage = True
	hasCenterLastPage = True
	if not num_pages in range(start, end+1):
		hasLastPage = False
		lastCenter = (end+num_pages) // 2
		if lastCenter >= num_pages-1:
			hasCenterLastPage = True
		else: 
			hasCenterLastPage = False

	# generating paginated list
	if not hasFirstPage:
		pages_list.append(1)
		pages_list.append(None)		
	if not hasCenterFirstPage:
		pages_list.append(firstCenter)
		pages_list.append(None)
		
	for i in range(start, end+1):
		pages_list.append(i)

	if not hasCenterLastPage:
		pages_list.append(None)
		pages_list.append(lastCenter)
	if not hasLastPage:
		pages_list.append(None)
		pages_list.append(num_pages)
		
	return pages_list
	
