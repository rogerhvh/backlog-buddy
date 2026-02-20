
"""
RUN THIS MODULE IF YOU WOULD LIKE TO RUN A MANUAL REBUILD
OF THE INDEX. 
"""

from data.index import Index

if __name__ == "__main__":
    i = Index()
    i.update_index()
