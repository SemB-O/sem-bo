import { Text, View, useWindowDimensions } from 'react-native';
import { useColorScheme } from 'react-native';
import { Colors } from '../constants/Colors';

type BrandTitleProps = {
  beforeText: string;
  highlight: string;
  afterText?: string;
  breakLineOnMobile?: boolean;
  sizeClass?: string; // ex: "text-4xl", "text-6xl"
  align?: 'left' | 'center' | 'right';
};

export default function BrandTitle({
  beforeText,
  highlight,
  afterText = '',
  breakLineOnMobile = false,
  sizeClass = 'text-6xl',
  align = 'center',
}: BrandTitleProps) {
  const colorScheme = useColorScheme();
  const logoBlue = Colors[colorScheme ?? 'light'].logoBlue;
  const { width } = useWindowDimensions();

  const isMobile = width < 768;
  const shouldBreakLine = breakLineOnMobile && isMobile;

  const justifyMap = {
    left: 'items-start',
    center: 'items-center',
    right: 'items-end',
  };

  const textAlignMap = {
    left: 'text-left',
    center: 'text-center',
    right: 'text-right',
  };

  const containerClasses = shouldBreakLine
    ? `w-full px-4 ${justifyMap[align]}`
    : `flex-row flex-wrap justify-center px-4`;

  const textCommonClasses = `tracking-tight leading-tight ${sizeClass} ${textAlignMap[align]}`;

  return (
    <View className={containerClasses}>
      <Text className={`${textCommonClasses} text-black`}>
        {beforeText}
      </Text>

      <Text
        className={`${textCommonClasses} font-extrabold`}
        style={{ color: logoBlue }}
      >
        {highlight}
      </Text>

      {afterText !== '' && (
        <Text className={`${textCommonClasses} text-black`}>
          {afterText}
        </Text>
      )}
    </View>
  );
}
