def main():
    with open('app/templates/customer/new_booking.html', 'r', encoding='utf-8') as f:
        text = f.read()

    text = text.replace(
        '''                                            <div class="searchable-dropdown" id="originDropdown"></div>
                                        </div>
                        </div>''',
        '''                                            <div class="searchable-dropdown" id="originDropdown"></div>
                                        </div>
                                    </div>
                                </div>
                        </div>'''
    )

    text = text.replace(
        '''                                            <div class="searchable-dropdown" id="destDropdown"></div>
                                        </div>
                        </div>''',
        '''                                            <div class="searchable-dropdown" id="destDropdown"></div>
                                        </div>
                                    </div>
                                </div>
                        </div>'''
    )

    with open('app/templates/customer/new_booking.html', 'w', encoding='utf-8') as f:
        f.write(text)

    print("Fixed HTML")

if __name__ == '__main__':
    main()
